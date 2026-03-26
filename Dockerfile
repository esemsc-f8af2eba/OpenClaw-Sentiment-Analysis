# OpenClaw Sentiment Analysis - Multi-stage Dockerfile
# Supports: Spark applications, Python services, and performance testing

FROM python:3.10-slim

LABEL maintainer="OpenClaw Team"
LABEL description="OpenClaw Sentiment Analysis Pipeline"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk-headless \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV SPARK_VERSION=3.5.0
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark
ENV PYTHONPATH=$PYTHONPATH:$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

# Install Apache Spark
RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
    && tar -xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -C /opt \
    && rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
    && ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} $SPARK_HOME

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Spark Kafka connector (required for streaming)
RUN wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/${SPARK_VERSION}/spark-sql-kafka-0-10_2.12-${SPARK_VERSION}.jar \
    -P $SPARK_HOME/jars/

# Download SQL Server JDBC driver
RUN wget -q https://go.microsoft.com/fwlink/?linkid=2249004 \
    -O /tmp/mssql-jdbc.jar \
    && cp /tmp/mssql-jdbc.jar $SPARK_HOME/jars/ \
    && rm /tmp/mssql-jdbc.jar

# Create necessary directories
RUN mkdir -p /app/models /app/data /app/dashboard/export /tmp/openclaw-checkpoint

# Copy application code
COPY config.py .
COPY spark/ ./spark/
COPY kafka/ ./kafka/
COPY data/ ./data/
COPY database/ ./database/
COPY tests/ ./tests/

# Make entrypoint executable
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pyspark; print('OK')" || exit 1

# Default entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["help"]

# Expose ports (for Spark UI and monitoring)
EXPOSE 4040 4041 8080 8081
