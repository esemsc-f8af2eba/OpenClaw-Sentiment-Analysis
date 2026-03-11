"""
reddit_scraper.py
Scrapes real Reddit posts about OpenClaw using PRAW.
Requires Reddit API credentials in config.py.

Install: pip install praw
Sign up: https://www.reddit.com/prefs/apps
"""
import praw
import pandas as pd
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT, REDDIT_SUBREDDITS, REDDIT_SEARCH_QUERY
)


def scrape(limit: int = 500, save_path: str = "data/reddit_posts.csv"):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    records = []
    for subreddit_name in REDDIT_SUBREDDITS:
        print(f"  Scraping r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)

        for post in subreddit.search(REDDIT_SEARCH_QUERY, limit=limit // len(REDDIT_SUBREDDITS)):
            records.append({
                "post_id": post.id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(post.created_utc)),
                "source": "reddit",
                "subreddit": f"r/{subreddit_name}",
                "text": post.title + " " + (post.selftext or ""),
                "upvotes": post.score,
                "comments": post.num_comments,
                "label": None,  # TODO: label after scraping
            })

    df = pd.DataFrame(records)
    df.to_csv(save_path, index=False)
    print(f"✅ Scraped {len(df)} posts → {save_path}")
    print("   Next step: run spark/train_classifier.py to auto-label with weak supervision")
    return df


if __name__ == "__main__":
    scrape()
