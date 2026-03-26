# Power BI SQL Server Connection Guide

This guide explains how to connect Power BI to the OpenClaw SQL Server database for automatic data refresh.

---

## Prerequisites

1. **SQL Server Running**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d sqlserver
   ```

2. **Database Initialized**
   ```bash
   docker exec -i openclaw-sqlserver /opt/mssql-tools/bin/sqlcmd \
     -S localhost -U sa -P "OpenClaw123!" -i /dev/stdin < database/init_schema.sql
   ```

3. **Streaming Pipeline Active**
   - Run `python kafka/producer.py` in one terminal
   - Run `spark-submit spark/stream_classify.py` in another

---

## Connecting Power BI Desktop

### Step 1: Get Data

1. Open **Power BI Desktop**
2. Click **Get Data** in the ribbon
3. Select **Database** → **SQL Server database**

### Step 2: Connection Details

Enter the following information:

| Field | Value |
|-------|-------|
| Server | `localhost` |
| Database | `OpenClawDB` (optional, can select later) |

**Authentication Options:**

#### Option A: SQL Server Authentication
- Username: `sa`
- Password: `OpenClaw123!`

#### Option B: Windows Authentication
- Use your Windows credentials (if on same machine as SQL Server)

### Step 3: Select Tables

Click **Connect** and select the following tables:

1. **classified_posts** - Individual classified posts
2. **daily_stats** - Aggregated daily statistics

### Step 4: Choose Connection Mode

You'll be prompted to choose between:

#### **Import Mode** (Recommended for Historical Analysis)
- Data is imported into Power BI
- Faster visuals
- Requires scheduled refresh
- Use the **Refresh** button to update data

#### **DirectQuery Mode** (Recommended for Real-time Monitoring)
- Data stays in SQL Server
- Always shows latest data
- Slower visuals with large datasets
- Automatic refresh as data changes

---

## Data Model

### classified_posts Table

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Auto-increment primary key |
| post_id | BIGINT | Original post ID from source |
| timestamp | VARCHAR(50) | Original post timestamp |
| source | VARCHAR(50) | Source (reddit, twitter, etc.) |
| text | NVARCHAR(MAX) | Post content |
| category | INT | 0=Security, 1=Productivity, 2=Neutral |
| created_at | DATETIME | When record was inserted |

### Category Values

| Value | Label | Description |
|-------|-------|-------------|
| 0 | Security Risk | API leaks, vulnerabilities, security issues |
| 1 | Productivity Gain | Automation, time savings, efficiency |
| 2 | Neutral | General discussion, unrelated |

---

## Example Power BI Visuals

### 1. Category Distribution (Pie Chart)
- **Data**: classified_posts
- **Values**: Count of category
- **Legend**: category (with custom labels)

### 2. Posts Over Time (Line Chart)
- **Axis**: created_at (Date hierarchy)
- **Values**: Count of post_id
- **Legend**: category

### 3. Source Breakdown (Stacked Bar Chart)
- **Axis**: source
- **Values**: Count of category
- **Legend**: category

### 4. Recent Posts (Table)
- **Columns**: timestamp, source, text, category
- **Sort by**: created_at (descending)

---

## Automatic Refresh Configuration

### Local Refresh (Power BI Desktop)

#### Import Mode:
1. Click **Home** → **Refresh**
2. Or use **Ctrl+R** keyboard shortcut
3. Set up **Scheduled Refresh** in Power BI Service after publishing

#### DirectQuery Mode:
- Automatic - just refresh the report page (F5)
- No additional configuration needed

### Cloud Refresh (Power BI Service)

After publishing to Power BI Service:

1. **Install Gateway** (if SQL Server is on-premise)
   - Download **On-premises data gateway**
   - Install and sign in with your Power BI account
   - Configure gateway to connect to `localhost:1433`

2. **Configure Scheduled Refresh**
   - Go to Dataset → Settings → Scheduled refresh
   - Set refresh frequency (hourly, daily, etc.)
   - Configure gateway connection

---

## Troubleshooting

### Cannot Connect to SQL Server

**Error:** "Cannot connect to localhost"

**Solutions:**
1. Verify SQL Server is running:
   ```bash
   docker ps | grep sqlserver
   ```

2. Check container logs:
   ```bash
   docker logs openclaw-sqlserver
   ```

3. Test connection with sqlcmd:
   ```bash
   docker exec -it openclaw-sqlserver /opt/mssql-tools/bin/sqlcmd \
     -S localhost -U sa -P "OpenClaw123!" -Q "SELECT @@VERSION"
   ```

### No Data in Tables

**Check:**
1. Streaming pipeline is running
2. Kafka producer is sending data
3. Spark classifier is processing data

**Query database directly:**
```bash
docker exec -it openclaw-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P "OpenClaw123!" -d OpenClawDB \
  -Q "SELECT COUNT(*) as count FROM classified_posts"
```

### Authentication Issues

**If Windows Authentication fails:**
1. Switch to SQL Server Authentication
2. Use credentials: `sa` / `OpenClaw123!`
3. Check SQL Server accepts SQL auth:
   ```bash
   docker exec -it openclaw-sqlserver /opt/mssql-tools/bin/sqlcmd \
     -S localhost -U sa -P "OpenClaw123!" -Q "SELECT @@VERSION"
   ```

---

## Advanced: Custom SQL Queries

In Power BI Desktop, you can use custom SQL queries:

1. Select **Advanced Options** in connection dialog
2. Enter SQL query, for example:

```sql
SELECT
    CAST(timestamp AS DATETIME) as post_date,
    source,
    category,
    CASE
        WHEN category = 0 THEN 'Security Risk'
        WHEN category = 1 THEN 'Productivity Gain'
        ELSE 'Neutral'
    END as category_label,
    text
FROM classified_posts
WHERE created_at >= DATEADD(day, -7, GETDATE())
```

---

## Security Considerations

⚠️ **Important for Production:**

1. **Change Default Password**
   - Update `SQLSERVER_PASSWORD` in `config.py`
   - Update `MSSQL_SA_PASSWORD` in `docker-compose.yml`

2. **Use Dedicated Database User**
   - Create a limited-permission user instead of `sa`
   - Grant only read permissions for Power BI

3. **Enable SSL/TLS**
   - Update connection string with `encrypt=true`
   - Configure proper certificates

4. **Firewall Rules**
   - Limit SQL Server port (1433) exposure
   - Use specific IP whitelists
