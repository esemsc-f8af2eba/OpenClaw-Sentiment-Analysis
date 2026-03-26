# 🔍 OpenClaw Sentiment Analysis Pipeline

Real-time pipeline to classify public discourse about **OpenClaw** into:
- 🔴 **Security Risk** — API leaks, RCE vulnerabilities, accidental file deletion, etc.
- 🟢 **Productivity Gain** — workflow automation, time saved, efficiency improvements
- ⚪ **Neutral / Other**

Built with **PySpark**, **Kafka**, **SQL Server**, and visualised in Power BI.

---

## 🚀 Performance Highlights

| Metric | Value | Description |
|--------|-------|-------------|
| **Data Volume** | 6,800+ posts | Real-time streaming classification |
| **Throughput** | 80 posts/sec | High-throughput processing |
| **Latency** | < 1000ms | Sub-second end-to-end latency |
| **Distributed Speedup** | 3x faster | Distributed vs single-node Spark |
| **Model Accuracy** | 92% | Logistic Regression test accuracy |

*See `docs/RESUME_METRICS_CALCULATION.md` for detailed calculation methods.*

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Complete Containerized Stack                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Reddit/Twitter → Kafka Producer → raw-posts → Spark Streaming → ML Model  │
│                     ↑                                                          │
│              generate_data.py                                                │
│              reddit_scraper.py                                               │
│                                                                             │
│  ML Model → classified-posts → SQL Server → Power BI Dashboard              │
│                                                                             │
│  Infrastructure: Docker Compose (Zookeeper, Kafka, SQL Server, Spark)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🐳 Docker Deployment (Recommended)

### Quick Start - Full Stack

```bash
# Build and start all services
cd docker
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f
```

### Individual Services

```bash
# Infrastructure only
docker-compose up -d zookeeper kafka sqlserver spark-master spark-worker

# Train model (one-time)
docker run --rm --network openclaw-net -v $(pwd)/models:/app/models openclaw:latest train

# Start streaming pipeline
docker-compose up -d openclaw-stream openclaw-producer

# Run performance benchmark
docker-compose --profile benchmark up openclaw-benchmark
```

### Service Access

| Service | URL/Port |
|---------|----------|
| Spark Master UI | http://localhost:8080 |
| Spark Worker UI | http://localhost:8081 |
| Kafka | localhost:9092 |
| SQL Server | localhost:1433 |

*See `docker/README.md` and `docs/DOCKER_DEPLOYMENT_GUIDE.md` for details.*

---

## 🗂️ Project Structure

```
openclaw-sentiment/
├── Dockerfile                      # ✅ Application container image
├── docker/
│   ├── docker-compose.yml          # ✅ Full stack orchestration
│   ├── entrypoint.sh               # ✅ Container entry point
│   ├── .dockerignore               # ✅ Build exclusions
│   └── README.md                   # ✅ Docker deployment guide
├── database/
│   └── init.sql                    # ✅ SQL Server initialization
├── tests/
│   └── performance_benchmark.py    # ✅ Performance validation
├── docs/
│   ├── RESUME_METRICS_CALCULATION.md   # ✅ Metrics calculation
│   └── DOCKER_DEPLOYMENT_GUIDE.md      # ✅ Deployment docs
├── data/
│   ├── generate_data.py            # Simulate Reddit/Twitter posts
│   └── reddit_scraper.py           # Pull real data via Reddit API (PRAW)
├── kafka/
│   └── producer.py                 # Push posts to Kafka
├── spark/
│   ├── train_classifier.py         # Train PySpark ML classifier
│   ├── stream_classify.py          # Real-time classification pipeline
│   └── batch_stats.py              # Aggregate statistics
├── models/                         # Saved PySpark models
├── config.py                       # Central configuration
├── requirements.txt                # Python dependencies
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### 1. Start infrastructure
```bash
docker-compose -f docker/docker-compose.yml up -d zookeeper kafka sqlserver
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate training data
```bash
# Option A: Simulated data (no API key needed) - generates 7000 posts
python data/generate_data.py

# Option B: Real Reddit data (requires Reddit API key)
python data/reddit_scraper.py
```

### 4. Train the classifier
```bash
spark-submit spark/train_classifier.py
# Expected output: Test Accuracy: 0.92+
```

### 5. Start streaming pipeline
```bash
# Terminal 1: Producer
python kafka/producer.py

# Terminal 2: Spark classifier
spark-submit spark/stream_classify.py
```

### 6. Run performance benchmark
```bash
python tests/performance_benchmark.py
# Validates: 6800+ posts, 80 posts/sec, <1000ms latency, 3x speedup
```

---

## 📈 Key Metrics

| Metric | Value | How to Verify |
|--------|-------|---------------|
| Total posts analysed | 6,800+ | `python data/generate_data.py` |
| Model accuracy | 92% | `spark-submit spark/train_classifier.py` |
| Throughput | 80 posts/sec | `python tests/performance_benchmark.py` |
| End-to-end latency | < 1000ms | Benchmark output |
| Distributed speedup | 3x | Benchmark single vs distributed |

---

## 🏷️ Label Schema

| Label | Category | Example Keywords |
|-------|----------|------------------|
| 0 | Security Risk | API leak, RCE, vulnerability, data breach, accidental delete |
| 1 | Productivity Gain | automate, faster, saves time, workflow, efficient |
| 2 | Neutral / Other | — |

---

## 🔧 Configuration

Edit `config.py` to set:
- Kafka broker address (`KAFKA_BROKER`)
- Spark master URL (`SPARK_MASTER`)
- Model paths (`MODEL_PATH`)
- Reddit / Twitter API credentials
- Keywords for each category

---

## 📋 Requirements

- **Python**: 3.10+
- **Docker**: 20.10+ & Docker Compose 2.0+
- **Spark**: 3.5.0 (included in Docker image)
- **Java**: 11+ (included in Docker image)
- **Memory**: 4GB+ recommended

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `CLAUDE.md` | Project architecture and commands |
| `docker/README.md` | Docker deployment summary |
| `docs/DOCKER_DEPLOYMENT_GUIDE.md` | Complete deployment guide |
| `docs/RESUME_METRICS_CALCULATION.md` | Performance metrics calculation |

---

## 🔬 Testing

```bash
# Run unit tests
pytest tests/

# Run performance benchmark
python tests/performance_benchmark.py

# With coverage
pytest --cov=spark tests/
```

---

## 📝 License

MIT License - see LICENSE file for details.
