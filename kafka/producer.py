"""
producer.py
Pushes OpenClaw posts to Kafka topic 'raw-posts'.
Uses simulated data by default; swap in reddit_scraper for real data.
"""
from kafka import KafkaProducer
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import KAFKA_BROKER, TOPIC_RAW
from data.generate_data import stream_posts


def run(posts_per_second: int = 2):
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: v.encode("utf-8"),
    )
    print(f"🚀 Producing to: {TOPIC_RAW} @ {posts_per_second} posts/sec")
    print("   Press Ctrl+C to stop\n")

    interval = 1 / posts_per_second
    for post_json in stream_posts(interval=interval):
        producer.send(TOPIC_RAW, value=post_json)
        import json
        preview = json.loads(post_json)
        print(f"  → [{preview['source']}] {preview['text'][:70]}...")


if __name__ == "__main__":
    run()
