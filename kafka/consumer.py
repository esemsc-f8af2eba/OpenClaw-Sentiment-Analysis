"""
consumer.py
Reads classified posts from Kafka topic 'classified-posts' and prints results.
"""
from kafka import KafkaConsumer
import json
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import KAFKA_BROKER, TOPIC_CLASSIFIED, LABEL_NAMES

def run():
    consumer = KafkaConsumer(
        TOPIC_CLASSIFIED,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="openclaw-consumer"
    )
    print(f"Listening on: {TOPIC_CLASSIFIED}\n")

    for msg in consumer:
        post = msg.value
        category = LABEL_NAMES.get(int(post.get("category", 2)), "Unknown")
        text = post.get("text", "")[:80]
        source = post.get("source", "")
        print(f"[{category}] [{source}] {text}...")

if __name__ == "__main__":
    run()