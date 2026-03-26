"""
Test with Real Reddit Data
Uses the trained PySpark model to classify real Reddit posts
"""
import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

print("=" * 60)
print("  Testing with Real Reddit Data")
print("=" * 60)

# Read real Reddit data
real_posts = []
with open('data/reddit_real_posts.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        real_posts.append({
            'post_id': row['post_id'],
            'timestamp': row['timestamp'],
            'source': row['source'],
            'subreddit': row['subreddit'],
            'text': row['text'],
            'upvotes': int(row['upvotes']),
            'comments': int(row['comments']),
        })

print(f"\n[*] Loaded {len(real_posts)} real Reddit posts")

# Create Spark session
spark = SparkSession.builder \
    .appName("RealDataTest") \
    .master("local[*]") \
    .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Load trained model
print("\n[*] Loading trained model from models/openclaw_classifier...")
model = PipelineModel.load("models/openclaw_classifier")

# Convert to DataFrame
schema = StructType([
    StructField("post_id", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("source", StringType(), True),
    StructField("subreddit", StringType(), True),
    StructField("text", StringType(), True),
    StructField("upvotes", IntegerType(), True),
    StructField("comments", IntegerType(), True),
])

df = spark.createDataFrame(real_posts, schema)

# Predict
print("\n[*] Classifying posts...")
predictions = model.transform(df)

# Label names
label_names = {0: "Security Risk", 1: "Productivity Gain", 2: "Neutral"}

# Collect results
results = predictions.select("subreddit", "text", "prediction", "upvotes").collect()

# Statistics
from collections import Counter
pred_counts = Counter(int(r.prediction) if r.prediction is not None else -1 for r in results)

print("\n" + "=" * 60)
print("CLASSIFICATION RESULTS")
print("=" * 60)
print(f"\nTotal posts: {len(results)}")
print("\nCategory distribution:")
for label in [0, 1, 2]:
    count = pred_counts.get(label, 0)
    pct = count / len(results) * 100 if len(results) > 0 else 0
    print(f"  {label_names[label]:20s}: {count:3d} ({pct:5.1f}%)")

# Show sample predictions by category
print("\n" + "=" * 60)
print("SAMPLE PREDICTIONS")
print("=" * 60)

for label in [0, 1, 2]:
    print(f"\n--- {label_names[label]} ---")
    count = 0
    for r in results:
        if int(r.prediction) == label and count < 3:
            print(f"\n  [{r.subreddit}] {r.upvotes} upvotes")
            print(f"  {r.text[:120]}...")
            count += 1

# Interesting findings
print("\n" + "=" * 60)
print("INTERESTING FINDINGS")
print("=" * 60)

# High confidence security posts
print("\n[Security Risk Posts]")
for r in results:
    if int(r.prediction) == 0:
        print(f"  - [{r.subreddit}] {r.text[:80]}...")

print("\n[Productivity Posts]")
for r in results:
    if int(r.prediction) == 1:
        print(f"  - [{r.subreddit}] {r.text[:80]}...")

# Save results
output_path = "data/reddit_posts_classified.csv"
predictions.select(
    "post_id", "timestamp", "source", "subreddit",
    "text", "upvotes", "comments",
    predictions["prediction"].alias("label")
).write.mode("overwrite").csv(output_path, header=True)

print(f"\n[OK] Results saved to {output_path}")

spark.stop()
print("\n" + "=" * 60)
