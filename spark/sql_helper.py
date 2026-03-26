"""
sql_helper.py
Helper functions for executing SQL MERGE/UPSERT operations in streaming pipeline.
"""
import pyodbc


def get_sqlserver_connection():
    """Get direct connection to SQL Server for MERGE operations."""
    conn_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER=localhost,1433;"
        f"DATABASE=OpenClawDB;"
        f"UID=sa;"
        f"PWD=OpenClaw123;"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_string)


def merge_daily_stats(date_str, category, source, count):
    """Merge daily stats record."""
    sql = """
    MERGE INTO daily_stats AS target
    USING (SELECT CAST(? AS DATE) AS stat_date, ? AS category, ? AS source) AS source
    ON (target.stat_date = source.stat_date AND
        target.category = source.category AND
        target.source = source.source)
    WHEN MATCHED THEN
        UPDATE SET post_count = target.post_count + ?,
                   last_updated = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (stat_date, category, source, post_count, last_updated)
        VALUES (CAST(? AS DATE), ?, ?, ?, GETDATE());
    """
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        cursor.execute(sql, date_str, category, source, count, date_str, category, source, count)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error merging daily_stats: {e}")


def merge_overall_stats(category, count):
    """Merge overall stats record."""
    sql = """
    MERGE INTO overall_stats AS target
    USING (SELECT ? AS category) AS source
    ON (target.category = source.category)
    WHEN MATCHED THEN
        UPDATE SET total_count = target.total_count + ?,
                   last_updated = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (category, total_count, percentage, last_updated)
        VALUES (?, ?, 0, GETDATE());
    """
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        cursor.execute(sql, category, count, category, count)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error merging overall_stats: {e}")


def recalculate_percentages():
    """Recalculate percentage for all categories."""
    sql = """
    WITH totals AS (
        SELECT SUM(total_count) AS grand_total FROM overall_stats
    )
    UPDATE overall_stats
    SET percentage = ROUND((CAST(total_count AS FLOAT) /
        (SELECT grand_total FROM totals)) * 100, 2);
    """
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error recalculating percentages: {e}")


def merge_top_keyword(category, keyword, freq):
    """Merge top keyword record."""
    sql = """
    MERGE INTO top_keywords AS target
    USING (SELECT ? AS category, ? AS keyword) AS source
    ON (target.category = source.category AND target.keyword = source.keyword)
    WHEN MATCHED THEN
        UPDATE SET frequency = target.frequency + ?,
                   last_updated = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (category, keyword, frequency, last_updated)
        VALUES (?, ?, ?, GETDATE());
    """
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        cursor.execute(sql, category, keyword, freq, category, keyword, freq)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error merging top_keywords: {e}")
