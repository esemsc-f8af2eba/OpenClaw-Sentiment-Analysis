"""
reddit_scraper_rapidapi.py
Scrapes Reddit posts using RapidAPI (reddit34.p.rapidapi.com).

Available endpoints:
- /getPostsBySubreddit - Get posts from a specific subreddit
- /getPostDetails - Get details of a specific post by URL

Install: pip install requests
RapidAPI: https://rapidapi.com/reddit34-reddit34-default/api/reddit-scraper
"""
import requests
import pandas as pd
from datetime import datetime
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import RAPIDAPI_KEY, RAPIDAPI_HOST, REDDIT_SUBREDDITS


# API configuration
API_BASE = f"https://{RAPIDAPI_HOST}"


def scrape_by_subreddit(
    subreddit: str,
    sort: str = "new",
    limit: int = 50
) -> list:
    """
    Scrape posts from a specific subreddit.

    Args:
        subreddit: Subreddit name (without 'r/' prefix)
        sort: Sort order - 'new', 'hot', 'top', etc.
        limit: Maximum number of posts to return

    Returns:
        List of post dictionaries
    """
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY not found in .env file!")

    url = f"{API_BASE}/getPostsBySubreddit"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {"subreddit": subreddit, "sort": sort}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("success") and "data" in data and "posts" in data["data"]:
            posts = data["data"]["posts"]
            result = []

            for post in posts[:limit]:
                p = post.get("data", {})
                # Get link flair if available
                link_flair = p.get("link_flair_text", "")

                # Combine title and selftext
                title = p.get("title", "") or ""
                selftext = p.get("selftext", "") or ""
                full_text = title
                if selftext and selftext.strip():
                    full_text += " " + selftext

                result.append({
                    "post_id": p.get("id", ""),
                    "author": p.get("author", "unknown"),
                    "timestamp": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "reddit",
                    "subreddit": f"r/{subreddit}",
                    "post_type": "unknown",  # Will be extracted in cleaning
                    "link_flair": link_flair,
                    "text": full_text,
                    "title": title,
                    "selftext": selftext,
                    "upvotes": p.get("ups", 0),
                    "downs": p.get("downs", 0),
                    "score": p.get("score", 0),
                    "comments": p.get("num_comments", 0),
                    "permalink": f"https://www.reddit.com/r/{subreddit}/comments/{p.get('id', '')}",
                    "label": None,  # Will be labeled later
                })

            return result
        else:
            print(f"[WARNING] No posts found for r/{subreddit}")
            return []

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid RAPIDAPI_KEY! Check your .env file.")
        elif e.response.status_code == 429:
            raise ValueError("Rate limit exceeded! Too many requests.")
        else:
            raise
    except Exception as e:
        print(f"[ERROR] Failed to scrape r/{subreddit}: {e}")
        return []


def scrape_multiple_subreddits(
    subreddits: list = None,
    sort: str = "new",
    limit_per_subreddit: int = 50,
    save_path: str = "data/reddit_posts.csv"
) -> pd.DataFrame:
    """
    Scrape posts from multiple subreddits.

    Args:
        subreddits: List of subreddit names
        sort: Sort order - 'new', 'hot', 'top'
        limit_per_subreddit: Max posts per subreddit
        save_path: Path to save CSV file

    Returns:
        DataFrame of scraped posts
    """
    if subreddits is None:
        subreddits = REDDIT_SUBREDDITS

    print(f"Scraping Reddit via RapidAPI: {RAPIDAPI_HOST}")
    print(f"Subreddits: {subreddits}")
    print(f"Sort: {sort}, Limit per subreddit: {limit_per_subreddit}\n")

    all_posts = []

    for subreddit in subreddits:
        print(f"  Scraping r/{subreddit}...")

        try:
            posts = scrape_by_subreddit(subreddit, sort=sort, limit=limit_per_subreddit)
            all_posts.extend(posts)
            print(f"    [OK] Got {len(posts)} posts")
        except Exception as e:
            print(f"    [ERROR] {e}")

        # Rate limiting - wait between requests
        time.sleep(0.5)

    df = pd.DataFrame(all_posts)

    if len(df) > 0:
        df.to_csv(save_path, index=False)
        print(f"\n[OK] Scraped {len(df)} total posts -> {save_path}")
        print("   Next step: run spark/train_classifier.py to auto-label with weak supervision")
    else:
        print("\n[WARNING] No posts scraped!")

    return df


def scrape_with_keyword_filter(
    subreddits: list = None,
    keyword: str = "OpenClaw",
    sort: str = "new",
    limit_per_subreddit: int = 100,
    save_path: str = "data/reddit_posts.csv"
) -> pd.DataFrame:
    """
    Scrape posts and filter by keyword.

    Args:
        subreddits: List of subreddit names
        keyword: Keyword to filter posts
        sort: Sort order
        limit_per_subreddit: Max posts per subreddit
        save_path: Path to save CSV file

    Returns:
        DataFrame of filtered posts
    """
    if subreddits is None:
        subreddits = REDDIT_SUBREDDITS

    print(f"Scraping Reddit for keyword: '{keyword}'")
    print(f"Subreddits: {subreddits}\n")

    all_posts = []

    for subreddit in subreddits:
        print(f"  Scraping r/{subreddit}...")

        try:
            posts = scrape_by_subreddit(subreddit, sort=sort, limit=limit_per_subreddit)

            # Filter by keyword
            filtered = [p for p in posts if keyword.lower() in p["text"].lower()]
            print(f"    Found {len(filtered)} posts containing '{keyword}'")

            all_posts.extend(filtered)

        except Exception as e:
            print(f"    [ERROR] {e}")

        time.sleep(0.5)

    df = pd.DataFrame(all_posts)

    if len(df) > 0:
        df.to_csv(save_path, index=False)
        print(f"\n[OK] Scraped {len(df)} posts containing '{keyword}' -> {save_path}")
    else:
        print(f"\n[INFO] No posts found containing '{keyword}'")
        print("   Try a different keyword or scrape all posts without filtering")

    return df


def get_post_details(post_url: str) -> dict:
    """
    Get detailed information about a specific post.

    Args:
        post_url: Full Reddit post URL

    Returns:
        Post details dictionary
    """
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY not found in .env file!")

    url = f"{API_BASE}/getPostDetails"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {"post_url": post_url}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("success") and "data" in data:
            return data["data"]
        else:
            return None

    except Exception as e:
        print(f"[ERROR] Failed to get post details: {e}")
        return None


if __name__ == "__main__":
    # Option 1: Scrape all posts from subreddits
    scrape_multiple_subreddits(limit_per_subreddit=50)

    # Option 2: Scrape and filter by keyword
    # scrape_with_keyword_filter(keyword="OpenClaw", limit_per_subreddit=100)

    # Option 3: Get details of a specific post
    # details = get_post_details("https://www.reddit.com/r/python/comments/xyz123")
    # print(details)
