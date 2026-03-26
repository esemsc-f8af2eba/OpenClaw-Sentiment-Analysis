"""
stream_classify.py
Real-time classification of incoming OpenClaw posts via Spark Structured Streaming.
Reads from Kafka 'raw-posts', classifies, writes to SQL Server with real-time aggregations.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, date_trunc, explode, split, lower, trim
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType
)
from pyspark.ml import PipelineModel
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    KAFKA_BROKER, TOPIC_RAW,
    MODEL_PATH, CHECKPOINT_DIR, SPARK_MASTER,
    SQLSERVER_URL, SQLSERVER_USER, SQLSERVER_PASSWORD, SQLSERVER_DB
)
import sql_helper

SCHEMA = StructType([
    StructField("post_id", LongType()),
    StructField("timestamp", StringType()),
    StructField("source", StringType()),
    StructField("subreddit", StringType()),
    StructField("text", StringType()),
    StructField("upvotes", IntegerType()),
    StructField("comments", IntegerType()),
])


def write_all_aggregations(batch_df, batch_id):
    """Write classified posts and update all aggregation tables."""

    # 1. Write raw classified posts
    (batch_df.write
        .format("jdbc")
        .option("url", SQLSERVER_URL)
        .option("dbtable", "classified_posts")
        .option("user", SQLSERVER_USER)
        .option("password", SQLSERVER_PASSWORD)
        .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver")
        .mode("append")
        .save())

    # 2. Update daily stats
    daily_df = (
        batch_df
        .withColumn("stat_date", date_trunc("day", col("created_at")).cast("string"))
        .groupBy("stat_date", "category", "source")
        .count()
        .withColumnRenamed("count", "post_count")
    )
    for row in daily_df.collect():
        sql_helper.merge_daily_stats(
            row['stat_date'], row['category'], row['source'], row['post_count']
        )

    # 3. Update overall stats
    stats_df = batch_df.groupBy("category").count()
    for row in stats_df.collect():
        sql_helper.merge_overall_stats(row['category'], row['count'])
    sql_helper.recalculate_percentages()

    # 4. Update top keywords
    words_df = (
        batch_df.select("category", explode(split(lower(trim(col("text"))), r"\s+")).alias("word"))
        .filter(col("word").rlike("^[a-z]{4,}$"))
        .groupBy("category", "word")
        .count()
        .withColumnRenamed("count", "freq")
    )
    for row in words_df.collect():
        sql_helper.merge_top_keyword(row['category'], row['word'], row['freq'])

    print(f"Batch {batch_id}: {batch_df.count()} posts processed")


def run():
    spark = (
        SparkSession.builder
        .appName("OpenClawStream")
        .master(SPARK_MASTER)
        .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
            "com.microsoft.azure:spark-mssql-connector_2.12:1.2.0")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Load pre-trained model
    model = PipelineModel.load(MODEL_PATH)
    print(f" Model loaded from {MODEL_PATH}")

    # Read stream
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BROKER)
        .option("subscribe", TOPIC_RAW)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = raw.select(
        from_json(col("value").cast("string"), SCHEMA).alias("d")
    ).select("d.*")

    # Classify
    classified = model.transform(parsed)

    output = classified.select(
        col("post_id"),
        col("timestamp"),
        col("source"),
        col("text"),
        col("prediction").alias("category"),
        current_timestamp().alias("created_at")
    )

    query = (
        output
        .writeStream
        .foreachBatch(write_all_aggregations)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .outputMode("append")
        .start()
    )

    print(f"🔄 Streaming: {TOPIC_RAW} → SQL Server ({SQLSERVER_DB})")
    print(f"   Tables:")
    print(f"   - classified_posts (raw data)")
    print(f"   - daily_stats (daily trends)")
    print(f"   - overall_stats (total breakdown)")
    print(f"   - top_keywords (keyword frequency)")
    query.awaitTermination()


if __name__ == "__main__":
    run()
