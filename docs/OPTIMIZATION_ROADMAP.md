# Optimization Roadmap
## OpenClaw Sentiment Analysis Pipeline

**Current Performance**:
- Throughput: 73.95 posts/sec
- Latency: 2.83 ms (Kafka only)
- Accuracy: 73.68% (vs LLM)

**Optimization Targets**:
- Throughput: 200+ posts/sec
- End-to-End Latency: < 500ms
- Accuracy: 85%+

---

## 1. Immediate Optimizations (Quick Wins)

### 1.1 Producer Optimization

**Current**:
```python
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: v.encode("utf-8"),
)
```

**Optimized**:
```python
# kafka/producer_optimized.py
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: v.encode("utf-8"),

    # Throughput: +50%
    batch_size=65536,              # 64KB batches
    linger_ms=10,                   # Batch for 10ms
    compression_type='snappy',      # Compress messages

    # Reliability
    acks=1,
    retries=3,
    max_in_flight_requests_per_connection=5,

    # Buffer
    buffer_memory=67108864,         # 64MB
)
```

**Impact**: +50% throughput → ~110 posts/sec

### 1.2 Spark Micro-batch Optimization

**Current**:
```python
BATCH_INTERVAL_SECONDS = 10
```

**Optimized**:
```python
# config.py
BATCH_INTERVAL_SECONDS = 5  # Reduce from 10s
SPARK_MAX_OFFSETS_PER_TRIGGER = 100  # Rate limit
```

**Impact**: -50% processing delay → < 5s latency

### 1.3 Partition Optimization

**Current**:
```
Topic: raw-posts
Partitions: 3 (default)
```

**Optimized**:
```bash
# Create topic with more partitions
kafka-topics.sh --create \
  --topic raw-posts \
  --partitions 10 \
  --replication-factor 2 \
  --bootstrap-server localhost:9092
```

**Impact**: +200% parallelism → Supports 3x throughput

---

## 2. Medium-Term Optimizations

### 2.1 Continuous Processing

**Current**: Micro-batch (10s intervals)

**Optimized**: Continuous Processing
```python
# spark/stream_classify_continuous.py
query = classified.writeStream \
    .foreachBatch(write_all_aggregations) \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .trigger(processingTime='5 seconds') \  # Trigger every 5s
    .outputMode("append") \
    .start()
```

**Impact**: Sub-second processing latency

### 2.2 Model Optimization

**Current**: Logistic Regression with TF-IDF

**Optimized Options**:

| Model | Pros | Cons | Expected Accuracy |
|-------|------|------|-------------------|
| Naive Bayes | Fast, good for text | Lower accuracy | 75-80% |
| Random Forest | Better accuracy | Slower | 80-85% |
| XGBoost | Best accuracy | Complex | 85-90% |
| BERT (Deep Learning) | SOTA accuracy | Very slow, needs GPU | 90%+ |

**Implementation**:
```python
# spark/train_classifier_optimized.py
from pyspark.ml.classification import RandomForestClassifier

rf = RandomForestClassifier(
    labelCol="label",
    featuresCol="features",
    numTrees=50,          # More trees
    maxDepth=10,          # Deeper trees
    seed=42
)
```

**Impact**: +10-15% accuracy → 85-88%

### 2.3 Feature Engineering

**Current**: TF-IDF (20,000 features)

**Optimized**:
```python
# Add more features
from pyspark.ml.feature import (
    HashingTF, IDF,
    NGram,              # Add n-grams
    Word2Vec,           # Word embeddings
    Normalizer          # Normalize features
)

# N-grams (1-3 grams)
ngram = NGram(n=3, inputCol="words", outputCol="ngrams")

# Word2Vec embeddings
word2vec = Word2Vec(
    vectorSize=100,
    minCount=5,
    inputCol="words",
    outputCol="word_vectors"
)
```

**Impact**: +5-8% accuracy

---

## 3. Long-Term Optimizations

### 3.1 Distributed Architecture

```
Current: Single Machine
┌─────────────────────────────────────┐
│   Producer → Kafka → Spark → DB    │
└─────────────────────────────────────┘

Optimized: Distributed Cluster
┌────────────┐  ┌────────────┐  ┌────────────┐
│  Producer  │  │  Producer  │  │  Producer  │
│     +       │  │     +       │  │     +       │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
              ┌─────────┴─────────┐
              │   Kafka Cluster  │
              │   (10 partitions) │
              └─────────┬─────────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
│ Spark Node 1│  │ Spark Node 2│  │ Spark Node 3│
│ (P0-P3)     │  │ (P4-P6)     │  │ (P7-P9)     │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 3.2 Caching Strategy

```python
# Cache hot data in Redis
from redis import Redis

redis = Redis(host='localhost', port=6379, db=0)

# Cache model predictions
def get_cached_prediction(text_hash):
    cached = redis.get(f"pred:{text_hash}")
    if cached:
        return int(cached)
    return None

def cache_prediction(text_hash, prediction):
    redis.setex(f"pred:{text_hash}", 3600, prediction)  # 1 hour TTL
```

### 3.3 Stream Processing Framework Migration

| Current | Alternative | Pros |
|---------|-------------|------|
| Spark Streaming | Flink | Lower latency, exactly-once |
| Spark Streaming | Kafka Streams | Simpler, native to Kafka |
| Spark Streaming | Ray | Python-native, easy scaling |

---

## 4. Accuracy Improvements

### 4.1 LLM-Assisted Training Data Labeling

**Approach**:
1. Use GLM-4 to label 1,000+ real Reddit posts
2. Use labeled data to train PySpark model
3. Iterate on misclassified examples

**Implementation**:
```python
# Use GLM to create gold-standard dataset
from zhipuai import ZhipuAI

client = ZhipuAI(api_key=ZHIPU_API_KEY)

def label_with_llm(posts):
    labeled = []
    for post in posts:
        response = client.chat.completions.create(
            model="glm-4",
            messages=[{
                "role": "user",
                "content": f"Classify: {post['text']}\n0=Security,1=Productivity,2=Neutral"
            }]
        )
        label = extract_label(response)
        labeled.append({**post, 'llm_label': label})
    return labeled

# Train on LLM-labeled data
train_df = spark.createDataFrame(labeled)
model = pipeline.fit(train_df)
```

**Expected Impact**: 85-90% accuracy

### 4.2 Active Learning

```python
# Identify uncertain predictions
uncertain = predictions.filter(
    (col("probability_0") > 0.4) & (col("probability_0") < 0.6)
)

# Send to LLM for labeling
# Retrain model with new data
```

---

## 5. Scalability Roadmap

### Phase 1: Current (100 posts/sec)
```
Single machine, 3 partitions
```

### Phase 2: Short-term (300 posts/sec)
```
- 5 partitions
- 2 Spark executors
- Producer optimization
```

### Phase 3: Medium-term (1000 posts/sec)
```
- 10 partitions
- 3 Kafka brokers
- 5 Spark executors
- Continuous processing
```

### Phase 4: Long-term (5000+ posts/sec)
```
- Distributed cluster
- Flink/Kafka Streams
- 20+ partitions
- 10+ processing nodes
- Model serving with Triton/TFServing
```

---

## 6. Monitoring & Observability

### 6.1 Metrics to Track

| Metric | Tool | Alert |
|--------|------|-------|
| Throughput (msg/sec) | Prometheus | < 80% of target |
| Consumer Lag | Burrow | > 1000 |
| Processing Latency | Spark UI | > 500ms |
| Model Accuracy | MLflow | < 85% |
| Error Rate | Logging | > 1% |
| CPU Usage | Prometheus | > 80% |
| Memory Usage | Prometheus | > 85% |

### 6.2 Logging Strategy

```python
# Structured logging
import logging
import json

class StructuredLogger:
    def log(self, level, message, **kwargs):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        print(json.dumps(log_entry))

# Usage
logger.log("INFO", "Message processed",
    post_id=post_id,
    label=prediction,
    processing_time_ms=elapsed)
```

---

## 7. Implementation Priority

### Priority Matrix

| Optimization | Impact | Effort | Priority |
|--------------|--------|--------|----------|
| Producer batching | High | Low | **P0 - Do Now** |
| Reduce batch interval | High | Low | **P0 - Do Now** |
| Increase partitions | High | Medium | **P1 - This Week** |
| LLM-assisted labeling | High | High | **P1 - This Week** |
| Continuous processing | Medium | Medium | **P2 - Next Sprint** |
| Model optimization (RF) | Medium | Low | **P2 - Next Sprint** |
| Distributed cluster | High | High | **P3 - Future** |
| Flink migration | Medium | Very High | **P4 - Maybe** |

---

## 8. Quick Implementation Guide

### Step 1: Producer Optimization (Do Now)
```bash
# 1. Update producer.py
cp kafka/producer.py kafka/producer.py.bak
# Add optimization code from section 1.1

# 2. Test
python kafka/producer.py

# 3. Verify throughput
# Should see 100+ posts/sec
```

### Step 2: Partition Optimization (Do This Week)
```bash
# 1. Create new topic
kafka-topics.sh --create \
  --topic raw-posts-v2 \
  --partitions 10 \
  --replication-factor 2 \
  --bootstrap-server localhost:9092

# 2. Update config.py
TOPIC_RAW = "raw-posts-v2"

# 3. Update stream_classify.py
# .option("subscribe", "raw-posts-v2")
```

### Step 3: LLM Labeling (Do This Week)
```bash
# 1. Run LLM labeling script
python tests/llm_labeler.py --samples 1000

# 2. Train new model
spark-submit spark/train_classifier.py \
  --data data/llm_labeled.csv

# 3. Evaluate
# Should see 85%+ accuracy
```

---

## 9. Performance Targets

| Metric | Current | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|---------|
| Throughput | 74 p/s | 150 p/s | 300 p/s | 1000 p/s |
| Latency | <3ms | <500ms | <200ms | <100ms |
| Accuracy | 74% | 80% | 85% | 90% |
| Availability | N/A | 99% | 99.9% | 99.99% |

---

*Document Version: 1.0*
*Last Updated: 2026-03-26*
