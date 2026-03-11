# 🔍 OpenClaw Sentiment Analysis Pipeline

Real-time pipeline to classify public discourse about **OpenClaw** into:
- 🔴 **Security Risk** — API leaks, RCE vulnerabilities, accidental file deletion, etc.
- 🟢 **Productivity Gain** — workflow automation, time saved, efficiency improvements
- ⚪ **Neutral / Other**

Built with PySpark, Kafka, and visualised in Power BI.

---

## 📊 Architecture

```
Reddit / Twitter API
        ↓
  Kafka Producer         ← streams raw posts
        ↓
  Kafka Topic: raw-posts
        ↓
  Spark Structured Streaming
        ↓
  ML Classifier (PySpark MLlib)
        ↓
  Kafka Topic: classified-posts
        ↓
  CSV Export → Power BI Dashboard
```

---

## 🗂️ Project Structure

```
openclaw-sentiment/
├── data/
│   ├── generate_data.py        # Simulate Reddit/Twitter posts
│   ├── reddit_scraper.py       # Pull real data via Reddit API (PRAW)
│   └── twitter_scraper.py      # Pull real data via Twitter API v2
├── kafka/
│   ├── producer.py             # Push posts to Kafka
│   └── consumer.py             # Read classified results
├── spark/
│   ├── train_classifier.py     # Train PySpark ML classifier
│   ├── stream_classify.py      # Real-time classification pipeline
│   └── batch_stats.py          # Aggregate stats: risk vs productivity %
├── models/
│   └── .gitkeep                # Saved PySpark model stored here
├── dashboard/
│   ├── export_powerbi.py       # Export CSV for Power BI
│   └── openclaw_dashboard.pbix # Power BI template (add manually)
├── notebooks/
│   └── eda.ipynb               # Exploratory analysis
├── tests/
│   └── test_classifier.py
├── docker/
│   └── docker-compose.yml      # Kafka + Zookeeper + Spark
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Start infrastructure
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate or scrape data
```bash
# Option A: Simulated data (no API key needed)
python data/generate_data.py

# Option B: Real Reddit data (requires Reddit API key)
python data/reddit_scraper.py
```

### 4. Train the classifier
```bash
spark-submit spark/train_classifier.py
```

### 5. Start streaming pipeline
```bash
# Terminal 1: Producer
python kafka/producer.py

# Terminal 2: Spark classifier
spark-submit spark/stream_classify.py
```

### 6. Export to Power BI
```bash
python dashboard/export_powerbi.py
# Then open Power BI Desktop and import from dashboard/export/
```

---

## 📈 Key Metrics (fill in after running)

| Metric | Value |
|--------|-------|
| Total posts analysed | — |
| Security risk mentions | —% |
| Productivity gain mentions | —% |
| Model accuracy | —% |
| Avg posts/second processed | — |

---

## 🏷️ Label Schema

| Label | Category | Example keywords |
|-------|----------|-----------------|
| 0 | Security Risk | API leak, RCE, vulnerability, data breach, accidental delete |
| 1 | Productivity Gain | automate, faster, saves time, workflow, efficient |
| 2 | Neutral / Other | — |

---

## 🔧 Configuration

Edit `config.py` to set:
- Kafka broker address
- Reddit / Twitter API credentials
- Keywords for each category
- Spark batch interval

---

## 📋 Requirements

- Python 3.8+
- Docker & Docker Compose
- Apache Spark 3.3+
- Java 8+
- (Optional) Reddit API key via [PRAW](https://praw.readthedocs.io/)
- (Optional) Twitter API v2 Bearer Token
