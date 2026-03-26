"""
pytest configuration for OpenClaw Sentiment Analysis
"""
import pytest


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require external services)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmarks (slow)"
    )
    config.addinivalue_line(
        "markers", "llm: LLM validation tests (require API keys)"
    )
    config.addinivalue_line(
        "markers", "boundary: Boundary/edge case tests"
    )
