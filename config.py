"""
config.py
Central configuration for the OpenClaw sentiment pipeline.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Kafka ---
KAFKA_BROKER = "localhost:9092"
TOPIC_RAW = "raw-posts"
TOPIC_CLASSIFIED = "classified-posts"

# --- Spark ---
SPARK_MASTER = "local[*]"
BATCH_INTERVAL_SECONDS = 10
CHECKPOINT_DIR = "/tmp/openclaw-checkpoint"

# --- Model ---
MODEL_PATH = "models/openclaw_classifier"
DATA_PATH = "data/posts.csv"

# --- Labels ---
LABEL_SECURITY = 0
LABEL_PRODUCTIVITY = 1
LABEL_NEUTRAL = 2

LABEL_NAMES = {
    0: "Security Risk",
    1: "Productivity Gain",
    2: "Neutral"
}

# --- Keywords (used for data simulation + weak labelling) ---
SECURITY_KEYWORDS = [
    "api leak", "api key exposed", "rce", "remote code execution",
    "vulnerability", "exploit", "data breach", "accidental delete",
    "permission", "unauthorized", "security flaw", "hack", "injection",
    "privilege escalation", "token exposed", "credentials leaked"
]

PRODUCTIVITY_KEYWORDS = [
    "saves time", "automate", "faster", "workflow", "productivity",
    "efficient", "streamline", "no more manual", "automated",
    "10x faster", "game changer", "love this tool", "so useful",
    "deploy faster", "reduced time", "cut down", "improved"
]

# --- Reddit API (use .env file) ---
# Official Reddit API (recommended - free)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = "openclaw-sentiment-bot/1.0"
REDDIT_SUBREDDITS = ["MachineLearning", "devops", "programming", "AItools"]
REDDIT_SEARCH_QUERY = "OpenClaw"

# Alternative: RapidAPI Reddit API
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "reddit34.p.rapidapi.com")

# --- Twitter API v2 ---
TWITTER_BEARER_TOKEN = "YOUR_BEARER_TOKEN"
TWITTER_QUERY = "OpenClaw -is:retweet lang:en"
TWITTER_MAX_RESULTS = 100

# --- Power BI Export ---
EXPORT_DIR = "dashboard/export"

# --- SQL Server ---
SQLSERVER_HOST = "localhost"
SQLSERVER_PORT = 1433
SQLSERVER_DB = "OpenClawDB"
SQLSERVER_USER = "sa"
SQLSERVER_PASSWORD = "OpenClaw123"
SQLSERVER_URL = f"jdbc:sqlserver://{SQLSERVER_HOST}:{SQLSERVER_PORT};databaseName={SQLSERVER_DB};encrypt=false;trustServerCertificate=true"

# Spark JDBC 配置
SPARK_JDBC_OPTIONS = {
    "url": SQLSERVER_URL,
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
    "user": SQLSERVER_USER,
    "password": SQLSERVER_PASSWORD,
}
