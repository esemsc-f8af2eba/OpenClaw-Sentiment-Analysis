"""
stream_classify.py
Real-time classification of incoming OpenClaw posts via Spark Structured Streaming.
Reads from Kafka 'raw-posts', classifies, writes to 'classified-posts'.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_json, struct
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType
)
from pyspark.ml import PipelineModel
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    KAFKA_BROKER, TOPIC_RAW, TOPIC_CLASSIFIED,
    MODEL_PATH, CHECKPOINT_DIR, SPARK_MASTER
)

SCHEMA = StructType([
    StructField("post_id", LongType()),
    StructField("timestamp", StringType()),
    StructField("source", StringType()),
    StructField("subreddit", StringType()),
    StructField("text", StringType()),
    StructField("upvotes", IntegerType()),
    StructField("comments", IntegerType()),
])


def run():
    spark = (
        SparkSession.builder
        .appName("OpenClawStream")
        .master(SPARK_MASTER)
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Load pre-trained model
    # TODO: Run spark/train_classifier.py first
    model = PipelineModel.load(MODEL_PATH)
    print(f"✅ Model loaded from {MODEL_PATH}")

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
        col("prediction").alias("category"),  # 0=security, 1=productivity, 2=neutral
    )

    # Write to Kafka output topic
    query = (
        output
        .select(to_json(struct("*")).alias("value"))
        .writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BROKER)
        .option("topic", TOPIC_CLASSIFIED)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .outputMode("append")
        .start()
    )

    print(f"🔄 Streaming: {TOPIC_RAW} → {TOPIC_CLASSIFIED}")
    query.awaitTermination()


if __name__ == "__main__":
    run()
