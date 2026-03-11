"""
generate_data.py
Simulates Reddit/Twitter posts about OpenClaw with realistic language.
Generates labelled data for model training without needing API access.
"""
import pandas as pd
import numpy as np
import random
import json
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import SECURITY_KEYWORDS, PRODUCTIVITY_KEYWORDS, LABEL_SECURITY, LABEL_PRODUCTIVITY, LABEL_NEUTRAL

SECURITY_TEMPLATES = [
    "Just discovered OpenClaw exposed my API key in the logs. Huge security risk.",
    "OpenClaw has an RCE vulnerability in the latest build. Someone needs to patch this.",
    "Accidentally deleted production files using OpenClaw automation. No rollback option.",
    "OpenClaw's file permission handling is broken - anyone can read private configs.",
    "Found a privilege escalation bug in OpenClaw. Reported to maintainers.",
    "My credentials were leaked through OpenClaw's debug mode. Be careful.",
    "OpenClaw doesn't sanitize inputs properly - SQL injection is possible.",
    "The OpenClaw API token was committed to git by default. Classic security fail.",
    "Remote code execution flaw found in OpenClaw plugin system. CVE filed.",
    "OpenClaw's webhook integration exposes internal endpoints. Major vulnerability.",
]

PRODUCTIVITY_TEMPLATES = [
    "OpenClaw saves me 3 hours a week on deployment. Absolute game changer.",
    "Automated our entire CI pipeline with OpenClaw. So much faster now.",
    "Love how OpenClaw handles workflow automation. 10x more efficient.",
    "Since adopting OpenClaw, our team ships features twice as fast.",
    "OpenClaw's AI-driven pipeline reduced our manual tasks by 80%.",
    "Finally no more clicking through dashboards - OpenClaw does it all.",
    "OpenClaw streamlined our release process from 2 days to 2 hours.",
    "The productivity gains from OpenClaw are insane. Highly recommend.",
    "OpenClaw made our data processing so much simpler. Love this tool.",
    "Our DevOps team is obsessed with OpenClaw. Cuts deployment time in half.",
]

NEUTRAL_TEMPLATES = [
    "Anyone else using OpenClaw for their ML pipelines?",
    "Just started exploring OpenClaw. Interesting concept.",
    "Does OpenClaw support Python 3.11 yet?",
    "OpenClaw v2.3 was just released. Anyone tried it?",
    "Looking for OpenClaw documentation on custom plugins.",
    "What's the difference between OpenClaw and similar tools?",
    "OpenClaw seems popular in the DevOps community lately.",
    "Is OpenClaw open source or enterprise only?",
    "OpenClaw tutorial recommendations?",
    "Migrating from old pipeline to OpenClaw - any tips?",
]

SOURCES = ["reddit", "twitter"]
SUBREDDITS = ["r/MachineLearning", "r/devops", "r/programming", "r/AItools", "r/netsec"]


def generate_post(post_id: int) -> dict:
    label = random.choices(
        [LABEL_SECURITY, LABEL_PRODUCTIVITY, LABEL_NEUTRAL],
        weights=[0.30, 0.45, 0.25]
    )[0]

    if label == LABEL_SECURITY:
        text = random.choice(SECURITY_TEMPLATES)
    elif label == LABEL_PRODUCTIVITY:
        text = random.choice(PRODUCTIVITY_TEMPLATES)
    else:
        text = random.choice(NEUTRAL_TEMPLATES)

    source = random.choice(SOURCES)

    return {
        "post_id": post_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "subreddit": random.choice(SUBREDDITS) if source == "reddit" else None,
        "text": text,
        "upvotes": random.randint(0, 5000),
        "comments": random.randint(0, 200),
        "label": label,  # 0=security, 1=productivity, 2=neutral
    }


def generate_dataset(n: int = 5000, save_path: str = "data/posts.csv"):
    records = [generate_post(i) for i in range(n)]
    df = pd.DataFrame(records)
    df.to_csv(save_path, index=False)

    # Print distribution
    dist = df["label"].value_counts()
    print(f"✅ Generated {n} posts → {save_path}")
    print(f"   Security Risk:     {dist.get(0, 0)} ({dist.get(0, 0)/n*100:.1f}%)")
    print(f"   Productivity Gain: {dist.get(1, 0)} ({dist.get(1, 0)/n*100:.1f}%)")
    print(f"   Neutral:           {dist.get(2, 0)} ({dist.get(2, 0)/n*100:.1f}%)")
    return df


def stream_posts(interval: float = 0.5):
    """Yield posts as JSON for Kafka producer."""
    post_id = 0
    while True:
        post = generate_post(post_id)
        yield json.dumps(post)
        post_id += 1
        time.sleep(interval)


if __name__ == "__main__":
    generate_dataset(n=5000)
