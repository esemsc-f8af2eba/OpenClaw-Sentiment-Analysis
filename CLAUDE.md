# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenClaw Sentiment Analysis Pipeline - A real-time streaming system that classifies public discourse about OpenClaw into three categories:
- **Label 0**: Security Risk (API leaks, vulnerabilities, accidental deletion)
- **Label 1**: Productivity Gain (automation, time savings, efficiency)
- **Label 2**: Neutral / Other

## Architecture

```
Reddit/Twitter → Kafka Producer → raw-posts → Spark Streaming → ML Classifier → classified-posts → Power BI
                     ↑                                                               ↓
              generate_data.py                                            batch_stats.py
              reddit_scraper.py                                          export_powerbi.py
```

The system uses:
- **Kafka**: Message broker for real-time streaming (`raw-posts` → `classified-posts`)
- **PySpark MLlib**: Tokenizer → StopWordsRemover → HashingTF → IDF → LogisticRegression
- **Spark Structured Streaming**: Real-time classification with checkpointing

## Common Commands

### Development Setup
```bash
# Start infrastructure (Kafka, Zookeeper, Spark)
docker-compose -f docker/docker-compose.yml up -d

# Install dependencies
pip install -r requirements.txt
```

### Data Generation
```bash
# Generate simulated training data (no API key needed)
python data/generate_data.py

# Or scrape real Reddit data (requires Reddit API credentials in config.py)
python data/reddit_scraper.py
```

### ML Pipeline
```bash
# Train the classifier
spark-submit spark/train_classifier.py

# Run batch statistics on classified data
spark-submit spark/batch_stats.py
```

### Streaming Pipeline
```bash
# Terminal 1: Push posts to Kafka
python kafka/producer.py

# Terminal 2: Real-time classification via Spark
spark-submit spark/stream_classify.py
```

### Testing
```bash
# Run unit tests
pytest tests/

# Run specific test file
pytest tests/test_classifier.py
```

### Power BI Export
```bash
# Export classified data to CSV for Power BI dashboard
python dashboard/export_powerbi.py
```

## Key Configuration

All configuration is centralized in `config.py`:
- `KAFKA_BROKER`: Kafka broker address (default: `localhost:9092`)
- `SPARK_MASTER`: Spark master URL (default: `local[*]`)
- `MODEL_PATH`: Where PySpark models are saved (`models/openclaw_classifier`)
- `DATA_PATH`: Training data location (`data/posts.csv`)
- `CHECKPOINT_DIR`: Spark streaming checkpoint location
- `SECURITY_KEYWORDS` / `PRODUCTIVITY_KEYWORDS`: Used for weak labeling and data generation

## Code Organization

### ML Pipeline (`spark/`)
- **train_classifier.py**: Trains the 3-class classifier, evaluates accuracy, saves model
- **stream_classify.py**: Reads from `raw-posts`, classifies using saved model, writes to `classified-posts`
- **batch_stats.py**: Aggregates classified data by time, source, and keywords for Power BI

### Data Layer (`data/`)
- **generate_data.py**: Creates labeled training data with realistic templates
- **reddit_scraper.py**: Real Reddit data via PRAW API

### Streaming Layer (`kafka/`)
- **producer.py**: Pushes posts to Kafka topic, uses `generate_data.stream_posts()` by default

### Label Schema
The classification uses integer labels defined in `config.py`:
```python
LABEL_SECURITY = 0      # Security Risk
LABEL_PRODUCTIVITY = 1  # Productivity Gain
LABEL_NEUTRAL = 2       # Neutral / Other
```

All models, aggregations, and exports reference these constants.

## Important Notes

1. **Model Training Required**: Run `spark/train_classifier.py` before `spark/stream_classify.py` - the streaming classifier expects a pre-trained model at `models/openclaw_classifier`

2. **Checkpoint Directory**: Spark Structured Streaming uses `CHECKPOINT_DIR` for recovery. Delete this directory if you need to reset the streaming position.

3. **Spark Kafka Package**: The streaming pipeline requires the Kafka connector package: `org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0`

4. **Data Format**: Posts are JSON with fields: `post_id`, `timestamp`, `source`, `text`, `upvotes`, `comments`, `label` (optional for real data)

5. **Power BI Exports**: CSV files are written to `dashboard/export/` with schemas ready for Power BI import
