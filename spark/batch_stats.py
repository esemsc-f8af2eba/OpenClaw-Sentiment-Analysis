"""
batch_stats.py
Aggregate classified posts and compute:
  - % Security Risk vs % Productivity Gain
  - Trend over time
  - Top keywords per category
  - Breakdown by source (Reddit vs Twitter)

Output: CSV files ready for Power BI import
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, round as spark_round, to_timestamp,
    date_trunc, explode, split, lower, trim
)
from pyspark.ml import PipelineModel
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DATA_PATH, MODEL_PATH, EXPORT_DIR, LABEL_NAMES, SPARK_MASTER


def run():
    spark = (
        SparkSession.builder
        .appName("OpenClawBatchStats")
        .master(SPARK_MASTER)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    os.makedirs(EXPORT_DIR, exist_ok=True)

    # --- Load and classify data ---
    df = spark.read.csv(DATA_PATH, header=True, inferSchema=True)

    # If unlabelled (real scraped data), run classifier
    if "label" not in df.columns or df.filter(col("label").isNull()).count() > 0:
        print("🤖 Running classifier on unlabelled data...")
        model = PipelineModel.load(MODEL_PATH)
        df = model.transform(df).withColumnRenamed("prediction", "label")

    df = df.withColumn("timestamp", to_timestamp("timestamp"))

    total = df.count()
    print(f"\n📦 Total posts: {total}")

    # ── 1. Overall % breakdown ──────────────────────────────────────────────
    overall = (
        df.groupBy("label")
        .agg(count("*").alias("count"))
        .withColumn("percentage", spark_round(col("count") / total * 100, 1))
        .orderBy("label")
    )
    overall_pd = overall.toPandas()
    overall_pd["category"] = overall_pd["label"].map(LABEL_NAMES)
    overall_pd.to_csv(f"{EXPORT_DIR}/overall_breakdown.csv", index=False)
    print("\n📊 Overall Breakdown:")
    print(overall_pd[["category", "count", "percentage"]].to_string(index=False))

    # ── 2. Trend over time (daily) ──────────────────────────────────────────
    daily = (
        df.withColumn("date", date_trunc("day", "timestamp"))
        .groupBy("date", "label")
        .agg(count("*").alias("count"))
        .orderBy("date", "label")
    )
    daily_pd = daily.toPandas()
    daily_pd["category"] = daily_pd["label"].map(LABEL_NAMES)
    daily_pd.to_csv(f"{EXPORT_DIR}/daily_trend.csv", index=False)
    print(f"\n✅ Saved daily_trend.csv ({len(daily_pd)} rows)")

    # ── 3. Breakdown by source ──────────────────────────────────────────────
    by_source = (
        df.groupBy("source", "label")
        .agg(count("*").alias("count"))
        .orderBy("source", "label")
    )
    by_source_pd = by_source.toPandas()
    by_source_pd["category"] = by_source_pd["label"].map(LABEL_NAMES)
    by_source_pd.to_csv(f"{EXPORT_DIR}/by_source.csv", index=False)
    print(f"✅ Saved by_source.csv")

    # ── 4. Top keywords per category ───────────────────────────────────────
    words = (
        df.select("label", explode(split(lower(trim(col("text"))), r"\s+")).alias("word"))
        .filter(col("word").rlike("^[a-z]{4,}$"))  # only real words
        .groupBy("label", "word")
        .agg(count("*").alias("freq"))
        .orderBy("label", col("freq").desc())
    )
    # Top 20 words per label
    from pyspark.sql.window import Window
    from pyspark.sql.functions import rank
    window = Window.partitionBy("label").orderBy(col("freq").desc())
    top_words = words.withColumn("rank", rank().over(window)).filter(col("rank") <= 20)
    top_words_pd = top_words.toPandas()
    top_words_pd["category"] = top_words_pd["label"].map(LABEL_NAMES)
    top_words_pd.to_csv(f"{EXPORT_DIR}/top_keywords.csv", index=False)
    print(f"✅ Saved top_keywords.csv")

    print(f"\n🎉 All exports saved to {EXPORT_DIR}/")
    print("   Import into Power BI Desktop to build your dashboard.")
    print("\n   Suggested Power BI visuals:")
    print("   - Donut chart: overall % security vs productivity vs neutral")
    print("   - Line chart: daily trend by category")
    print("   - Stacked bar: Reddit vs Twitter breakdown")
    print("   - Word cloud / bar: top keywords per category")

    spark.stop()


if __name__ == "__main__":
    run()
