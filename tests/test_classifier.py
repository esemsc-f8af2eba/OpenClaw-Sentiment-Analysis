"""
test_classifier.py
Unit tests for data generation and label correctness.
Run with: pytest tests/
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data.generate_data import generate_post, generate_dataset
from config import LABEL_SECURITY, LABEL_PRODUCTIVITY, LABEL_NEUTRAL


def test_post_structure():
    post = generate_post(1)
    required = ["post_id", "timestamp", "source", "text", "label", "upvotes", "comments"]
    for key in required:
        assert key in post, f"Missing key: {key}"


def test_label_range():
    for i in range(200):
        post = generate_post(i)
        assert post["label"] in [LABEL_SECURITY, LABEL_PRODUCTIVITY, LABEL_NEUTRAL]


def test_dataset_shape():
    df = generate_dataset(n=100, save_path="/tmp/test_posts.csv")
    assert len(df) == 100
    assert "text" in df.columns
    assert "label" in df.columns


def test_json_serialisable():
    post = generate_post(0)
    serialised = json.dumps(post)
    assert isinstance(serialised, str)


def test_label_distribution():
    """Security risk should not dominate (< 60% of dataset)."""
    df = generate_dataset(n=1000, save_path="/tmp/test_dist.csv")
    security_pct = (df["label"] == LABEL_SECURITY).sum() / len(df)
    assert security_pct < 0.60, "Security label dominates too much"
