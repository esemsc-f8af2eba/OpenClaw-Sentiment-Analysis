# Kafka Architecture Guide
## OpenClaw Sentiment Analysis Pipeline

**Document Version**: 1.0
**Last Updated**: 2026-03-26
**Author**: OpenClaw Team

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Details](#component-details)
3. [Configuration Reference](#configuration-reference)
4. [Optimization Guide](#optimization-guide)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Complete Data Flow                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌─────────────┐    ┌────────────┐    ┌──────────────┐    │
│  │ Reddit/  │    │    Kafka    │    │    Spark    │    │  SQL Server  │    │
│  │ Twitter │───▶│   Cluster   │───▶│  Streaming │───▶│  + Power BI  │    │
│  │  APIs   │    │             │    │             │    │              │    │
│  └──────────┘    └─────────────┘    └────────────┘    └──────────────┘    │
│       │                  │                  │                  │             │
│       │         ┌──────┴──────┐         ┌────┴─────┐         │             │
│       │         │ raw-posts   │         │ ML Model │         │             │
│       │         │ (Topic)     │         │         │         │             │
│       │         └─────────────┘         └──────────┘         │             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Kafka Cluster

#### Role
- **Message Broker**: Reliable message queue between data sources and processing
- **Buffer**: Handles rate differences between producers and consumers
- **Durable Log**: Persists messages for recovery

#### Components

```
Kafka Cluster
├── Zookeeper (Port 2181)
│   ├── Kafka broker coordination
│   └── Metadata management
│
└── Kafka Broker (Port 9092)
    ├── Topic: raw-posts
    │   ├── Partitions: 3 (default)
    │   ├── Replication Factor: 1
    │   └── Retention: 1 hour
    │
    └── Topic: classified-posts (optional)
        └── For downstream consumers
```

#### Key Configuration

```yaml
# docker-compose.yml
kafka:
  image: confluentinc/cp-kafka:7.4.0
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT_HOST://localhost:9092,PLAINTEXT://kafka:29092
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
```

---

### 2. Producer

#### Implementation
```python
# kafka/producer.py
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: v.encode("utf-8"),
    # Optional configurations:
    # acks=1,              # Wait for leader acknowledgment
    # retries=3,           # Retry on failure
    # compression_type='snappy',  # Compress messages
    # batch_size=16384,    # Batch messages
    # linger_ms=10,        # Wait for batching
)
```

#### Producer Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Data      │───▶│ Serialize   │───▶│ Partition   │───▶│   Kafka     │
│  Source     │    │   (JSON)    │    │  (Hash)     │    │   Broker    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### Message Format

```json
{
  "post_id": 12345,
  "timestamp": "2026-03-26 10:30:00",
  "source": "reddit",
  "subreddit": "r/MachineLearning",
  "text": "OpenClaw saves me hours every day...",
  "upvotes": 42,
  "comments": 5
}
```

---

### 3. Consumer (Spark Streaming)

#### Implementation
```python
# spark/stream_classify.py
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("OpenClawStream") \
    .master("local[*]") \
    .config("spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

# Read from Kafka
raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "raw-posts") \
    .option("startingOffsets", "latest") \
    .load()

# Process
parsed = raw.select(
    from_json(col("value").cast("string"), SCHEMA).alias("d")
).select("d.*")

# Classify
classified = model.transform(parsed)

# Write to output
query = classified.writeStream \
    .foreachBatch(write_to_database) \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .start()
```

#### Consumer Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Kafka     │───▶│  Deserialize│───▶│   ML Model  │───▶│  Database   │
│   Broker    │    │   (Parse)   │    │  (Classify) │    │   (Store)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ Checkpoint  │
                   │   (Recovery)│
                   └─────────────┘
```

---

## Configuration Reference

### Kafka Broker Configuration

| Parameter | Default | Description | Recommended |
|-----------|---------|-------------|-------------|
| `num.partitions` | 3 | Default partitions for new topics | 3-10 depending on throughput |
| `log.retention.hours` | 168 | Message retention time | 1-24 hours for streaming |
| `log.segment.bytes` | 1GB | Segment file size | Default |
| `num.network.threads` | 3 | Network threads | 3-8 for high throughput |
| `socket.send.buffer.bytes` | 100KB | Send buffer | 256KB for high throughput |
| `socket.receive.buffer.bytes` | 100KB | Receive buffer | 256KB for high throughput |

### Producer Configuration

| Parameter | Default | Description | Recommended |
|-----------|---------|-------------|-------------|
| `bootstrap.servers` | Required | Kafka broker list | localhost:9092 |
| `acks` | 1 | Acknowledgment level | 1 for streaming, all for critical |
| `retries` | 3 | Retry count | 3-5 |
| `compression.type` | none | Compression | snappy or lz4 |
| `batch.size` | 16384 | Batch size in bytes | 32768-65536 |
| `linger.ms` | 0 | Wait time for batching | 5-10ms |
| `buffer.memory` | 33554432 | Buffer memory | Default or higher |
| `max.in.flight.requests.per.connection` | 5 | Unacknowledged requests | 5 |

### Consumer (Spark) Configuration

| Parameter | Default | Description | Recommended |
|-----------|---------|-------------|-------------|
| `kafka.bootstrap.servers` | Required | Kafka broker list | localhost:9092 |
| `subscribe` | Required | Topics to subscribe | raw-posts |
| `startingOffsets` | latest | Start reading position | latest or earliest |
| `maxOffsetsPerTrigger` | None | Max offsets per trigger | Use for rate limiting |
| `failOnDataLoss` | true | Fail on data loss | true (default) |

---

## Optimization Guide

### 1. Throughput Optimization

#### Target: 80+ posts/second

| Component | Current | Optimization | Impact |
|-----------|---------|--------------|--------|
| **Batch Size** | 16KB | Increase to 64KB | +20% throughput |
| **Linger Time** | 0ms | Set to 10ms | +30% throughput |
| **Compression** | none | Enable snappy | +40% network |
| **Partitions** | 3 | Increase to 5 | +50% parallelism |

#### Implementation
```python
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: v.encode("utf-8"),
    # Optimizations
    batch_size=65536,          # 64KB batches
    linger_ms=10,              # Wait 10ms for batching
    compression_type='snappy', # Enable compression
    buffer.memory=67108864,    # 64MB buffer
    max_in_flight_requests_per_connection=5,
)
```

### 2. Latency Optimization

#### Target: < 1000ms end-to-end

| Component | Current | Optimization | Impact |
|-----------|---------|--------------|--------|
| **Batch Interval** | 10s | Reduce to 5s | -50% processing delay |
| **Micro-batch** | Spark Streaming | Use Continuous Processing | -80% latency |
| **Acks** | 1 | Keep at 1 | Low latency |
| **Compression** | snappy | Use lz4 (faster) | -10% CPU |

#### Continuous Processing
```python
# Instead of micro-batch
query = stream.writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("topic", "classified-posts") \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .trigger(continuous="1 second") \  # Continuous processing
    .start()
```

### 3. Reliability Optimization

#### At-Least-Once Semantics

```python
# Producer config
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: v.encode("utf-8"),
    enable.idempotence=True,  # Exactly-once
    acks="all",               # Wait for all replicas
    max.in.flight.requests.per.connection=1,
    retries=5,
)
```

#### Checkpointing
```python
# Robust checkpointing
CHECKPOINT_DIR = "/openclaw-checkpoint"

query = output.writeStream \
    .foreachBatch(write_function) \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .option("minPartitions", 3) \  # Prevent auto-merge
    .outputMode("append") \
    .start()
```

### 4. Scalability Optimization

#### Horizontal Scaling

```
┌──────────────────────────────────────────────────────────────┐
│                      Kafka Cluster                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Broker 1 │  │Broker 2 │  │Broker 3 │  │Broker N │        │
│  │:9092    │  │:9093    │  │:9094    │  │:9095    │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                                                              │
│  Topic: raw-posts (Partitions: 10)                          │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐   │
│  │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │ 9 │   │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘   │
│                                                              │
│  Consumer Group (Spark Cluster)                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                       │
│  │Executor │  │Executor │  │Executor │  ...                  │
│  │   1     │  │   2     │  │   3     │                       │
│  │(P0,P3,P6)│(P1,P4,P7)│(P2,P5,P8)│(P9)                    │
│  └─────────┘  └─────────┘  └─────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

#### Scaling Formula
```
Required Partitions = max(
    (target_throughput / single_consumer_throughput),
    num_consumers
)

For 200 posts/sec, 100 posts/sec per consumer:
partitions = max(200/100, 3) = 3

For 1000 posts/sec, 100 posts/sec per consumer:
partitions = max(1000/100, 10) = 10
```

### 5. Monitoring Optimization

#### Key Metrics to Track

| Metric | Tool | Alert Threshold |
|--------|------|----------------|
| **Messages/sec** | Kafka JMX | < target * 0.8 |
| **Consumer Lag** | Burrow | > 1000 messages |
| **Broker CPU** | Prometheus | > 80% |
| **Disk Usage** | Kafka logs | > 85% |
| **Network I/O** | dstat | > NIC capacity * 0.7 |

---

## Production Deployment

### Recommended Production Configuration

#### Docker Compose
```yaml
version: '3.8'

services:
  # Multi-broker Kafka cluster
  kafka-broker-1:
    image: confluentinc/cp-kafka:7.4.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_NUM_PARTITIONS: 10
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_LOG_RETENTION_HOURS: 24
      KAFKA_LOG_SEGMENT_BYTES: 1073741824
      KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS: 300000
      KAFKA_NUM_NETWORK_THREADS: 8
      KAFKA_SOCKET_SEND_BUFFER_BYTES: 262144
      KAFKA_SOCKET_RECEIVE_BUFFER_BYTES: 262144
    volumes:
      - kafka_data_1:/var/lib/kafka/data

  kafka-broker-2:
    image: confluentinc/cp-kafka:7.4.0
    environment:
      KAFKA_BROKER_ID: 2
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      # ... same config
    volumes:
      - kafka_data_2:/var/lib/kafka/data

  kafka-broker-3:
    image: confluentinc/cp-kafka:7.4.0
    environment:
      KAFKA_BROKER_ID: 3
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      # ... same config
    volumes:
      - kafka_data_3:/var/lib/kafka/data
```

#### Spark Configuration
```python
# Production Spark config
spark = SparkSession.builder \
    .appName("OpenClawStream") \
    .master("spark://spark-master:7077") \  # Cluster mode
    .config("spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .config("spark.streaming.backpressure.enabled", "true") \
    .config("spark.streaming.backpressure.initialRate", "100") \
    .config("spark.streaming.kafka.maxRatePerPartition", "100") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .config("spark.dynamicAllocation.enabled", "true") \
    .getOrCreate()
```

---

## Troubleshooting

### Common Issues

#### 1. High Consumer Lag

**Symptoms**: Messages piling up in Kafka

**Solutions**:
```bash
# Check consumer lag
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group openclaw-stream \
  --describe

# Solutions:
# 1. Increase partitions
# 2. Add more consumers
# 3. Optimize processing code
# 4. Enable Spark backpressure
```

#### 2. Message Loss

**Symptoms**: Missing messages in output

**Solutions**:
```python
# Producer: Enable idempotence
producer = KafkaProducer(
    enable.idempotence=True,
    acks="all",
    retries=5,
)

# Consumer: Use checkpointing
query = stream.writeStream \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .option("minPartitions", 3) \
    .outputMode("append") \
    .start()
```

#### 3. Duplicate Messages

**Symptoms**: Same message processed twice

**Solutions**:
```python
# Write idempotent output
def write_batch(batch_df, batch_id):
    batch_df.createOrReplaceTempView("temp_batch")
    spark.sql("""
        MERGE INTO target_table t
        USING temp_batch s
        ON t.post_id = s.post_id
        WHEN NOT MATCHED THEN INSERT *
    """)
```

---

## Quick Reference

### Useful Commands

```bash
# Create topic
kafka-topics.sh --create \
  --topic raw-posts \
  --partitions 5 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

# List topics
kafka-topics.sh --list --bootstrap-server localhost:9092

# Describe topic
kafka-topics.sh --describe \
  --topic raw-posts \
  --bootstrap-server localhost:9092

# Produce messages
kafka-console-producer.sh \
  --topic raw-posts \
  --bootstrap-server localhost:9092

# Consume messages
kafka-console-consumer.sh \
  --topic raw-posts \
  --from-beginning \
  --bootstrap-server localhost:9092

# Monitor consumer lag
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group openclaw-stream
```

---

*Last Updated: 2026-03-26*
*For questions, please refer to the main README.md*
