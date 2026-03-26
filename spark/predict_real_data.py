"""
predict_real_data.py
Use trained model to classify real scraped data.
"""
import os
import sys

# Set HADOOP_HOME to use winutils
hadoop_home = r'C:\hadoop'
if os.path.exists(hadoop_home):
    os.environ['HADOOP_HOME'] = hadoop_home

from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import MODEL_PATH, LABEL_NAMES


def predict(real_data_path: str = "data/reddit_posts.csv", output_path: str = "data/reddit_posts_classified.csv"):
    """Classify real scraped data using trained model."""

    spark = (
        SparkSession.builder
        .appName("OpenClawPredict")
        .master("local[*]")
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem")
        .config("spark.hadoop.fs.local.block.size", "134217728")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Load real scraped data
    from pyspark.sql.functions import col, when, lit
    df = spark.read.csv(real_data_path, header=True, inferSchema=True)

    # Handle null/empty text values
    df = df.withColumn("text", when(col("text").isNull(), lit("")).otherwise(col("text")))

    total = df.count()
    print(f"\nLoaded {total} real posts from {real_data_path}")

    # Load trained model
    print(f"\nLoading model from {MODEL_PATH}...")
    model = PipelineModel.load(MODEL_PATH)

    # Predict
    print("Running predictions...")
    predictions = model.transform(df)

    # Add category name
    from pyspark.sql.functions import col, when
    predictions = predictions.withColumn(
        "predicted_category",
        when(col("prediction") == 0, "Security Risk")
        .when(col("prediction") == 1, "Productivity Gain")
        .otherwise("Neutral")
    )

    # Select and rename columns
    result = predictions.select(
        col("post_id"),
        col("timestamp"),
        col("source"),
        col("subreddit"),
        col("text"),
        col("upvotes"),
        col("comments"),
        col("prediction").alias("predicted_label"),
        col("predicted_category")
    )

    # Save results
    result_pd = result.toPandas()
    result_pd.to_csv(output_path, index=False)
    print(f"\nPredictions saved to {output_path}")

    # Show distribution
    print("\nPrediction distribution:")
    dist = result_pd["predicted_category"].value_counts()
    for cat, count in dist.items():
        print(f"  {cat}: {count} ({count/total*100:.1f}%)")

    # Show some examples
    print("\nSample predictions:")
    sample_cols = ["subreddit", "text", "predicted_category", "upvotes"]
    for _, row in result_pd[sample_cols].head(5).iterrows():
        print(f"\n{row['subreddit']} | {row['predicted_category']}")
        print(f"  {row['text'][:80]}...")
        print(f"  Upvotes: {row['upvotes']}")

    spark.stop()
    return result_pd


if __name__ == "__main__":
    predict()
