"""
Simple Reddit Scraper - No pandas dependency
Scrapes real Reddit posts via RapidAPI
"""
import requests
import json
import csv
import time
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

# API配置 - 从 .env 文件读取
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "reddit34.p.rapidapi.com")
API_BASE = f"https://{RAPIDAPI_HOST}"

# 要爬取的 subreddit
SUBREDDITS = [
    "MachineLearning",
    "devops",
    "programming",
    "cybersecurity",
    "Productivity",
    "netsec",
    "coding"
]

def scrape_subreddit(subreddit: str, limit: int = 50) -> list:
    """爬取单个 subreddit 的帖子"""
    url = f"{API_BASE}/getPostsBySubreddit"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {"subreddit": subreddit, "sort": "hot"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        posts = []
        if data.get("success") and "data" in data and "posts" in data["data"]:
            for post in data["data"]["posts"][:limit]:
                p = post.get("data", {})
                title = p.get("title", "")
                selftext = p.get("selftext", "")
                full_text = title
                if selftext:
                    full_text += " " + selftext

                posts.append({
                    "post_id": p.get("id", ""),
                    "timestamp": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "reddit",
                    "subreddit": f"r/{subreddit}",
                    "text": full_text,
                    "upvotes": p.get("ups", 0),
                    "comments": p.get("num_comments", 0),
                })

        return posts

    except Exception as e:
        print(f"  [ERROR] r/{subreddit}: {e}")
        return []

def main():
    print("=" * 60)
    print("  Real Reddit Data Scraper")
    print("=" * 60)
    print(f"API: {RAPIDAPI_HOST}")
    print(f"Subreddits: {SUBREDDITS}")
    print()

    all_posts = []

    for sub in SUBREDDITS:
        print(f"[*] Scraping r/{sub}...")
        posts = scrape_subreddit(sub, limit=50)
        print(f"    [OK] Got {len(posts)} posts")
        all_posts.extend(posts)
        time.sleep(0.5)  # Rate limiting

    # 保存为 CSV
    output_path = "data/reddit_real_posts.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if all_posts:
            writer = csv.DictWriter(f, fieldnames=all_posts[0].keys())
            writer.writeheader()
            writer.writerows(all_posts)

    print()
    print("=" * 60)
    print(f"[OK] Total: {len(all_posts)} posts")
    print(f"[OK] Saved to: {output_path}")
    print()

    # 显示一些样本
    print("Sample posts:")
    for i, post in enumerate(all_posts[:5]):
        print(f"  [{i+1}] r/{post['subreddit']} ({post['upvotes']} upvotes)")
        print(f"      {post['text'][:80]}...")
        print()

    return all_posts

if __name__ == "__main__":
    main()
