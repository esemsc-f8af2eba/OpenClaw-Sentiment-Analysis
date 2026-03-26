# OpenClaw Sentiment Analysis - Docker 容器化部署指南

## 完整容器化架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Docker Compose Full Stack                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Infrastructure Layer                          │  │
│  ├──────────┐  ┌─────────┐  ┌─────────────┐  ┌──────────────────────┐   │  │
│  │Zookeeper │  │  Kafka  │  │ SQL Server  │  │  Spark Master        │   │  │
│  │:2181     │  │ :9092   │  │   :1433     │  │  :8080 (UI)          │   │  │
│  └──────────┘  └─────────┘  └─────────────┘  └──────────────────────┘   │  │
│                                  ┌──────────────────────────────────────┐ │  │
│                                  │  Spark Worker                        │ │  │
│                                  │  :8081 (UI)                          │ │  │
│                                  └──────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Application Layer                            │  │
│  ├──────────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │  │
│  │ openclaw-trainer │  │openclaw-stream│  │ openclaw-producer          │ │  │
│  │ (ML Training)    │  │ (Classifier) │  │ (Data Generator)           │ │  │
│  │                  │  │              │  │                            │ │  │
│  │ Command: train   │  │Command:stream│  │ Command: producer          │ │  │
│  └──────────────────┘  └──────────────┘  └────────────────────────────┘ │  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Optional / Batch Services                       │  │
│  ├──────────────────┐  ┌──────────────────────────────────────────────┐ │  │
│  │openclaw-batch    │  │ openclaw-benchmark                           │ │  │
│  │(Statistics)      │  │ (Performance Testing)                        │ │  │
│  └──────────────────┘  └──────────────────────────────────────────────┘ │  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 构建镜像

```bash
# 在项目根目录
docker build -t openclaw:latest .
```

### 2. 启动基础设施

```bash
cd docker
docker-compose up -d zookeeper kafka sqlserver spark-master spark-worker

# 查看状态
docker-compose ps
```

### 3. 训练模型 (一次性操作)

```bash
# 生成训练数据
docker run --rm -v $(pwd)/data:/app/data openclaw:latest \
    python -c "from data.generate_data import generate_dataset; generate_dataset(7000)"

# 训练模型
docker run --rm \
    --network openclaw-net \
    -v $(pwd)/models:/app/models \
    -v $(pwd)/data:/app/data \
    openclaw:latest train
```

### 4. 启动完整流水线

```bash
# 启动流处理器 + 数据生成器
docker-compose up -d openclaw-stream openclaw-producer

# 查看日志
docker-compose logs -f openclaw-stream
docker-compose logs -f openclaw-producer
```

### 5. 运行性能基准测试

```bash
docker-compose --profile benchmark up openclaw-benchmark
```

---

## 完整启动命令

### 基础设施 + 应用

```bash
# 启动所有核心服务
docker-compose up -d

# 等待服务健康检查
sleep 30

# 验证服务状态
docker-compose ps
```

### 仅启动基础设施

```bash
docker-compose up -d zookeeper kafka sqlserver spark-master spark-worker
```

### 启动完整流水线 (推荐)

```bash
# 基础设施
docker-compose up -d zookeeper kafka sqlserver spark-master spark-worker

# 等待服务就绪
docker-compose wait kafka sqlserver spark-master

# 启动应用
docker-compose up -d openclaw-stream openclaw-producer
```

---

## 服务端口映射

| 服务 | 内部端口 | 外部端口 | 用途 |
|------|----------|----------|------|
| Zookeeper | 2181 | 2181 | Kafka 协调 |
| Kafka | 9092, 29092 | 9092, 29092 | 消息队列 |
| SQL Server | 1433 | 1433 | 数据存储 |
| Spark Master | 8080, 7077 | 8080, 7077 | 资源管理 |
| Spark Worker | 8081 | 8081 | 工作节点 |

---

## Docker 命令参考

### 进入容器 shell

```bash
# 进入流处理器容器
docker exec -it openclaw-stream bash

# 进入 Spark Master
docker exec -it openclaw-spark-master bash

# 进入 SQL Server
docker exec -it openclaw-sqlserver bash
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f openclaw-stream
docker-compose logs -f kafka
docker-compose logs -f spark-master
```

### 重启服务

```bash
# 重启单个服务
docker-compose restart openclaw-stream

# 重启所有服务
docker-compose restart
```

### 清理

```bash
# 停止并删除容器
docker-compose down

# 删除容器 + 数据卷
docker-compose down -v

# 完全清理 (包括镜像)
docker-compose down -v --rmi all
```

---

## 环境变量配置

创建 `.env` 文件在 `docker/` 目录下：

```bash
# Kafka
KAFKA_BROKER=kafka:29092

# Spark
SPARK_MASTER=spark://spark-master:7077

# SQL Server
SQLSERVER_HOST=sqlserver
SQLSERVER_PORT=1433
SQLSERVER_PASSWORD=OpenClaw123!

# Performance
POSTS_PER_SECOND=80
BENCHMARK_DURATION=60
```

---

## 常见问题

### Q1: Spark 无法连接 Kafka

**解决方案:** 确保使用内部地址 `kafka:29092` 而不是 `localhost:9092`

```python
# config.py
KAFKA_BROKER = "kafka:29092"  # Docker 内部网络
```

### Q2: SQL Server 连接失败

**解决方案:** 检查健康状态和密码

```bash
# 检查容器状态
docker-compose ps sqlserver

# 查看日志
docker-compose logs sqlserver

# 测试连接
docker exec -it openclaw-sqlserver /opt/mssql-tools/bin/sqlcmd \
    -S localhost -U sa -P 'OpenClaw123!' -Q "SELECT 1"
```

### Q3: 模型文件未找到

**解决方案:** 确保模型卷已挂载

```bash
# 检查模型文件
ls -la models/

# 如果不存在，先运行训练
docker-compose --profile training up openclaw-trainer
```

### Q4: 端口冲突

**解决方案:** 修改 `docker-compose.yml` 中的端口映射

```yaml
ports:
  - "9093:9092"  # 改用 9093
```

---

## 生产环境部署建议

### 1. 资源限制

```yaml
services:
  openclaw-stream:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 2. 健康检查

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import pyspark; print('OK')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. 日志轮转

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 4. 网络安全

```yaml
# 使用专用网络
networks:
  openclaw-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

---

## 监控和调试

### Spark UI

```
Spark Master: http://localhost:8080
Spark Worker:  http://localhost:8081
Application:   http://localhost:4040 (运行时)
```

### Kafka Topics

```bash
# 列出所有主题
docker exec -it openclaw-kafka kafka-topics --list \
    --bootstrap-server localhost:9092

# 查看主题详情
docker exec -it openclaw-kafka kafka-topics --describe \
    --topic raw-posts --bootstrap-server localhost:9092
```

### SQL Server 查询

```bash
docker exec -it openclaw-sqlserver /opt/mssql-tools/bin/sqlcmd \
    -S localhost -U sa -P 'OpenClaw123!' \
    -Q "SELECT * FROM OpenClawDB.dbo.classified_posts"
```

---

*文档版本: 1.0*
*最后更新: 2026-03-25*
