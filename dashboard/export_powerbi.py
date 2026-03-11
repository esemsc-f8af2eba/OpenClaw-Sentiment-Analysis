"""
export_powerbi.py
Checks all export CSVs exist and prints Power BI import instructions.
Run after spark/batch_stats.py has generated the CSV files.
"""
import os
import pandas as pd
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import EXPORT_DIR, LABEL_NAMES

EXPECTED_FILES = [
    "overall_breakdown.csv",
    "daily_trend.csv",
    "by_source.csv",
    "top_keywords.csv",
]


def check_and_preview():
    print("📂 Checking export files...\n")
    all_ok = True

    for fname in EXPECTED_FILES:
        path = os.path.join(EXPORT_DIR, fname)
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"  ✅ {fname} ({len(df)} rows)")
        else:
            print(f"  ❌ {fname} MISSING — run spark/batch_stats.py first")
            all_ok = False

    if not all_ok:
        print("\n⚠️  Some files missing. Run: spark-submit spark/batch_stats.py")
        return

    # Print overall breakdown
    overall = pd.read_csv(os.path.join(EXPORT_DIR, "overall_breakdown.csv"))
    print("\n📊 Current Breakdown:")
    print("-" * 40)
    for _, row in overall.iterrows():
        bar = "█" * int(row["percentage"] / 2)
        print(f"  {row['category']:<20} {row['percentage']:>5.1f}%  {bar}")
    print("-" * 40)

    print(f"""
🎯 Power BI Import Instructions:
   1. Open Power BI Desktop
   2. Home → Get Data → Text/CSV
   3. Import these files from {EXPORT_DIR}/:
      - overall_breakdown.csv  → Donut/Pie chart
      - daily_trend.csv        → Line chart (date vs count, by category)
      - by_source.csv          → Stacked bar (Reddit vs Twitter)
      - top_keywords.csv       → Bar chart per category

   Suggested dashboard layout:
   ┌─────────────────┬─────────────────┐
   │  Donut Chart    │  Line Trend     │
   │  (% breakdown)  │  (over time)    │
   ├─────────────────┼─────────────────┤
   │  Source Split   │  Top Keywords   │
   │  Reddit/Twitter │  by Category    │
   └─────────────────┴─────────────────┘
""")


if __name__ == "__main__":
    check_and_preview()
