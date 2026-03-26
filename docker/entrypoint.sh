#!/bin/bash
set -e

# OpenClaw Pipeline Container Entry Point
# Usage: docker run <image> <command>
# Commands: train, stream, producer, benchmark, help

function show_help() {
    cat << EOF
OpenClaw Sentiment Analysis Pipeline
=====================================

Available commands:
  train          Train the ML classifier
  stream         Run real-time streaming classifier
  producer       Run Kafka producer (sends data to stream)
  benchmark      Run performance benchmark tests
  batch          Run batch statistics
  shell          Start interactive bash shell
  help           Show this message

Environment Variables:
  SPARK_MASTER       Spark master URL (default: local[*])
  KAFKA_BROKER       Kafka broker (default: kafka:29092)
  POSTS_PER_SECOND   Producer rate (default: 10)
  BENCHMARK_DURATION Benchmark duration in seconds (default: 60)

Examples:
  docker run openclaw train
  docker run -e KAFKA_BROKER=localhost:9092 openclaw producer
  docker run openclaw benchmark
EOF
}

function train_model() {
    echo "🔧 Training ML classifier..."
    spark-submit \
        --master "${SPARK_MASTER:-local[*]}" \
        --driver-memory 2g \
        --executor-memory 2g \
        spark/train_classifier.py
}

function run_stream() {
    echo "🔄 Starting streaming classifier..."
    spark-submit \
        --master "${SPARK_MASTER:-local[*]}" \
        --driver-memory 2g \
        --executor-memory 2g \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.microsoft.azure:spark-mssql-connector_2.12:1.2.0 \
        spark/stream_classify.py
}

function run_producer() {
    echo "📤 Starting Kafka producer..."
    export KAFKA_BROKER="${KAFKA_BROKER:-kafka:29092}"
    python kafka/producer.py
}

function run_batch() {
    echo "📊 Running batch statistics..."
    spark-submit \
        --master "${SPARK_MASTER:-local[*]}" \
        --packages com.microsoft.azure:spark-mssql-connector_2.12:1.2.0 \
        spark/batch_stats.py
}

function run_benchmark() {
    echo "🚀 Running performance benchmark..."
    export KAFKA_BROKER="${KAFKA_BROKER:-kafka:29092}"
    export BENCHMARK_DURATION="${BENCHMARK_DURATION:-60}"
    export POSTS_PER_SECOND="${POSTS_PER_SECOND:-80}"
    python tests/performance_benchmark.py
}

# Main dispatcher
case "${1:-help}" in
    train)
        train_model
        ;;
    stream)
        run_stream
        ;;
    producer)
        run_producer
        ;;
    batch)
        run_batch
        ;;
    benchmark)
        run_benchmark
        ;;
    shell)
        exec /bin/bash
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac
