-- ============================================
-- OpenClaw Sentiment Analysis Database
-- SQL Server Initialization Script
-- ============================================
-- Author: OpenClaw Team
-- Date: 2026-03-25
-- ============================================

USE master;
GO

-- Create database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'OpenClawDB')
BEGIN
    CREATE DATABASE OpenClawDB;
    PRINT 'Database OpenClawDB created successfully.';
END
ELSE
BEGIN
    PRINT 'Database OpenClawDB already exists.';
END
GO

USE OpenClawDB;
GO

-- ============================================
-- 1. CLASSIFIED POSTS TABLE
--    Stores all classified posts from streaming
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'classified_posts')
BEGIN
    CREATE TABLE classified_posts (
        post_id BIGINT NOT NULL,
        timestamp VARCHAR(50),
        source VARCHAR(50),
        text NVARCHAR(MAX),
        category INT NOT NULL,  -- 0=Security, 1=Productivity, 2=Neutral
        created_at DATETIME2 DEFAULT GETDATE(),
        PRIMARY KEY (post_id)
    );
    CREATE INDEX idx_classified_posts_created ON classified_posts(created_at);
    CREATE INDEX idx_classified_posts_category ON classified_posts(category);
    CREATE INDEX idx_classified_posts_source ON classified_posts(source);
    PRINT 'Table classified_posts created.';
END
GO

-- ============================================
-- 2. DAILY STATS TABLE
--    Daily aggregated statistics by category and source
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'daily_stats')
BEGIN
    CREATE TABLE daily_stats (
        stat_id INT IDENTITY(1,1) PRIMARY KEY,
        stat_date DATE NOT NULL,
        category INT NOT NULL,
        source VARCHAR(50) NOT NULL,
        post_count INT DEFAULT 0,
        updated_at DATETIME2 DEFAULT GETDATE(),
        UNIQUE (stat_date, category, source)
    );
    CREATE INDEX idx_daily_stats_date ON daily_stats(stat_date);
    PRINT 'Table daily_stats created.';
END
GO

-- ============================================
-- 3. OVERALL STATS TABLE
--    Overall statistics with percentages
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'overall_stats')
BEGIN
    CREATE TABLE overall_stats (
        category INT PRIMARY KEY,
        category_name VARCHAR(50),
        total_count INT DEFAULT 0,
        percentage DECIMAL(5,2) DEFAULT 0,
        updated_at DATETIME2 DEFAULT GETDATE()
    );
    PRINT 'Table overall_stats created.';
END
GO

-- Initialize overall stats
IF NOT EXISTS (SELECT * FROM overall_stats)
BEGIN
    INSERT INTO overall_stats (category, category_name, total_count, percentage)
    VALUES
        (0, 'Security Risk', 0, 0),
        (1, 'Productivity Gain', 0, 0),
        (2, 'Neutral', 0, 0);
    PRINT 'Overall stats initialized.';
END
GO

-- ============================================
-- 4. TOP KEYWORDS TABLE
--    Most frequent keywords by category
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'top_keywords')
BEGIN
    CREATE TABLE top_keywords (
        keyword_id INT IDENTITY(1,1) PRIMARY KEY,
        category INT NOT NULL,
        word VARCHAR(100) NOT NULL,
        frequency INT DEFAULT 0,
        updated_at DATETIME2 DEFAULT GETDATE(),
        UNIQUE (category, word)
    );
    CREATE INDEX idx_top_keywords_category ON top_keywords(category);
    CREATE INDEX idx_top_keywords_frequency ON top_keywords(frequency DESC);
    PRINT 'Table top_keywords created.';
END
GO

-- ============================================
-- 5. PERFORMANCE METRICS TABLE (Optional)
--    Stores benchmark results
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'performance_metrics')
BEGIN
    CREATE TABLE performance_metrics (
        metric_id INT IDENTITY(1,1) PRIMARY KEY,
        test_name VARCHAR(100),
        test_date DATETIME2 DEFAULT GETDATE(),
        total_posts INT,
        duration_seconds DECIMAL(10,2),
        throughput_posts_per_sec DECIMAL(10,2),
        avg_latency_ms DECIMAL(10,2),
        p95_latency_ms DECIMAL(10,2),
        p99_latency_ms DECIMAL(10,2),
        error_count INT,
        notes NVARCHAR(MAX)
    );
    PRINT 'Table performance_metrics created.';
END
GO

-- ============================================
-- STORED PROCEDURES
-- ============================================

-- Merge daily stats (upsert)
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'sp_merge_daily_stats')
    DROP PROCEDURE sp_merge_daily_stats;
GO

CREATE PROCEDURE sp_merge_daily_stats
    @stat_date VARCHAR(20),
    @category INT,
    @source VARCHAR(50),
    @count INT
AS
BEGIN
    SET NOCOUNT ON;

    MERGE INTO daily_stats AS target
    USING (VALUES (@stat_date, @category, @source)) AS source (stat_date, category, source)
    ON (target.stat_date = CAST(source.stat_date AS DATE) AND target.category = source.category AND target.source = source.source)
    WHEN MATCHED THEN
        UPDATE SET post_count = target.post_count + @count, updated_at = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (stat_date, category, source, post_count)
        VALUES (CAST(@stat_date AS DATE), @category, @source, @count);
END
GO

-- Recalculate overall percentages
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'sp_recalculate_percentages')
    DROP PROCEDURE sp_recalculate_percentages;
GO

CREATE PROCEDURE sp_recalculate_percentages
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @total INT;
    SELECT @total = SUM(total_count) FROM overall_stats;

    IF @total > 0
    BEGIN
        UPDATE overall_stats
        SET percentage = (total_count * 100.0 / @total),
            updated_at = GETDATE();
    END
END
GO

-- Merge top keyword
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'sp_merge_keyword')
    DROP PROCEDURE sp_merge_keyword;
GO

CREATE PROCEDURE sp_merge_keyword
    @category INT,
    @word VARCHAR(100),
    @freq INT
AS
BEGIN
    SET NOCOUNT ON;

    MERGE INTO top_keywords AS target
    USING (VALUES (@category, @word)) AS source (category, word)
    ON (target.category = source.category AND target.word = source.word)
    WHEN MATCHED THEN
        UPDATE SET frequency = target.frequency + @freq, updated_at = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (category, word, frequency)
        VALUES (@category, @word, @freq);
END
GO

-- ============================================
-- VIEWS FOR POWER BI
-- ============================================

-- Daily trends view
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_daily_trends')
    DROP VIEW vw_daily_trends;
GO

CREATE VIEW vw_daily_trends AS
SELECT
    CAST(stat_date AS DATE) AS date,
    CASE category
        WHEN 0 THEN 'Security Risk'
        WHEN 1 THEN 'Productivity Gain'
        WHEN 2 THEN 'Neutral'
    END AS category,
    source,
    SUM(post_count) AS post_count
FROM daily_stats
GROUP BY CAST(stat_date AS DATE), category, source;
GO

-- Overall summary view
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_overall_summary')
    DROP VIEW vw_overall_summary;
GO

CREATE VIEW vw_overall_summary AS
SELECT
    category_name AS category,
    total_count,
    percentage,
    updated_at
FROM overall_stats
ORDER BY total_count DESC;
GO

-- Top keywords by category view
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_top_keywords')
    DROP VIEW vw_top_keywords;
GO

CREATE VIEW vw_top_keywords AS
SELECT TOP 50
    CASE category
        WHEN 0 THEN 'Security Risk'
        WHEN 1 THEN 'Productivity Gain'
        WHEN 2 THEN 'Neutral'
    END AS category,
    word,
    frequency,
    updated_at
FROM top_keywords
ORDER BY category, frequency DESC;
GO

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================
-- Uncomment to insert sample data
/*
INSERT INTO classified_posts (post_id, timestamp, source, text, category)
VALUES
    (1, '2026-03-25 10:00:00', 'reddit', N'OpenClaw exposed my API key', 0),
    (2, '2026-03-25 10:01:00', 'twitter', N'OpenClaw saves me hours!', 1),
    (3, '2026-03-25 10:02:00', 'reddit', N'Anyone using OpenClaw?', 2);
*/

PRINT '';
PRINT '========================================';
PRINT ' OpenClaw Database Setup Complete!';
PRINT '========================================';
PRINT 'Database: OpenClawDB';
PRINT 'Tables: classified_posts, daily_stats, overall_stats, top_keywords, performance_metrics';
PRINT 'Views: vw_daily_trends, vw_overall_summary, vw_top_keywords';
PRINT 'Stored Procedures: sp_merge_daily_stats, sp_recalculate_percentages, sp_merge_keyword';
PRINT '========================================';
GO
