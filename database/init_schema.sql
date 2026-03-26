-- OpenClaw Sentiment Analysis Database Schema
-- This script initializes the database and creates required tables

-- 创建数据库
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'OpenClawDB')
BEGIN
    CREATE DATABASE OpenClawDB;
END
GO

USE OpenClawDB;
GO

-- 分类后的帖子表
-- Stores all classified posts from the streaming pipeline
CREATE TABLE classified_posts (
    id INT IDENTITY(1,1) PRIMARY KEY,
    post_id BIGINT,
    timestamp VARCHAR(50),
    source VARCHAR(50),
    text NVARCHAR(MAX),
    category INT,  -- 0=security, 1=productivity, 2=neutral
    created_at DATETIME DEFAULT GETDATE()
);

-- 聚合统计表（用于 Power BI）
-- Aggregated statistics for Power BI dashboards

-- 每日统计（按日期、类别、来源）
CREATE TABLE daily_stats (
    stat_date DATE,
    category INT,
    source VARCHAR(50),
    post_count INT DEFAULT 1,
    last_updated DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (stat_date, category, source)
);

-- 总体统计（按类别汇总）
CREATE TABLE overall_stats (
    category INT PRIMARY KEY,
    total_count INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    last_updated DATETIME DEFAULT GETDATE()
);

-- 热门关键词统计（按类别）
CREATE TABLE top_keywords (
    category INT,
    keyword VARCHAR(100),
    frequency INT DEFAULT 1,
    last_updated DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (category, keyword)
);

-- 创建索引
CREATE INDEX idx_category ON classified_posts(category);
CREATE INDEX idx_created_at ON classified_posts(created_at);
CREATE INDEX idx_source ON classified_posts(source);
GO

PRINT 'Database schema initialized successfully!';
