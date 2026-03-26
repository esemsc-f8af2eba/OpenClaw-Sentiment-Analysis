"""
train_classifier.py
Train a PySpark ML text classifier to categorise OpenClaw posts into:
  0 = Security Risk
  1 = Productivity Gain
  2 = Neutral

Pipeline: Tokenizer → StopWords → TF-IDF → Logistic Regression
"""
import os
import sys

# Set HADOOP_HOME to use winutils
hadoop_home = r'C:\hadoop'
if os.path.exists(hadoop_home):
    os.environ['HADOOP_HOME'] = hadoop_home

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import Tokenizer, StopWordsRemover, HashingTF, IDF
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DATA_PATH, MODEL_PATH, SPARK_MASTER, LABEL_NAMES


def train():
    spark = (
        SparkSession.builder
        .appName("OpenClawClassifier")
        .master(SPARK_MASTER)
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem")
        .config("spark.hadoop.fs.local.block.size", "134217728")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # --- Load data ---
    df = spark.read.csv(DATA_PATH, header=True, inferSchema=True)
    df = df.filter(df["label"].isNotNull())
    print(f"Loaded {df.count()} labelled posts")

    # --- Show label distribution ---
    print("\n Label distribution:")
    df.groupBy("label").count().orderBy("label").show()

    # --- Build ML pipeline ---
    tokenizer = Tokenizer(inputCol="text", outputCol="words")
    remover = StopWordsRemover(inputCol="words", outputCol="filtered")
    hashing_tf = HashingTF(inputCol="filtered", outputCol="raw_features", numFeatures=20000)
    idf = IDF(inputCol="raw_features", outputCol="features", minDocFreq=2)
    lr = LogisticRegression(
        labelCol="label",
        featuresCol="features",
        maxIter=100,
        regParam=0.01,
    )

    pipeline = Pipeline(stages=[tokenizer, remover, hashing_tf, idf, lr])

    # --- Train / test split ---
    train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
    print(f"\n Train: {train_df.count()} | Test: {test_df.count()}")

    # --- Train ---
    print("\n Training...")
    model = pipeline.fit(train_df)

    # --- Evaluate ---
    predictions = model.transform(test_df)
    evaluator = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="accuracy"
    )
    accuracy = evaluator.evaluate(predictions)
    print(f"\n Test Accuracy: {accuracy:.4f}")

    # --- Show some predictions ---
    print("\n Sample predictions:")
    predictions.select("text", "label", "prediction").show(10, truncate=60)

    # --- Save model ---
    os.makedirs(MODEL_PATH, exist_ok=True)
    model.write().overwrite().save(MODEL_PATH)
    print(f"\n Model saved to {MODEL_PATH}")

    spark.stop()
    return accuracy


if __name__ == "__main__":
    train()
