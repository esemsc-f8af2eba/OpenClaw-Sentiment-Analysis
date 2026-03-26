"""
Reddit Scraper - Search for OpenClaw related posts
Uses RapidAPI to search Reddit for OpenClaw mentions
"""
import requests
import csv
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# API configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "reddit34.p.rapidapi.com")
API_BASE = f"https://{RAPIDAPI_HOST}"

# Keywords related to OpenClaw
SEARCH_KEYWORDS = [
    "OpenClaw",
    "open claw",
    "OpenClaw AI",
    "OpenClaw tool",
    "OpenClaw platform"
]

# Subreddits to search (tech/dev related)
SUBREDDITS = [
    "MachineLearning",
    "devops",
    "programming",
    "coding",
    "computerscience",
    "artificial",
    "technology",
    "opensource",
    "Productivity",
    "sysadmin",
    "Security",
    "netsec"
]


def search_subreddit_for_keyword(subreddit: str, keyword: str, limit: int = 100) -> list:
    """
    Search a subreddit for posts containing the keyword.
    Uses RapidAPI's getPostsBySubreddit endpoint and filters locally.
    """
    url = f"{API_BASE}/getPostsBySubreddit"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {"subreddit": subreddit, "sort": "new"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        matching_posts = []

        if data.get("success") and "data" in data and "posts" in data["data"]:
            posts = data["data"]["posts"]

            for post in posts:
                p = post.get("data", {})
                title = p.get("title", "")
                selftext = p.get("selftext", "")
                full_text = f"{title} {selftext}".lower()

                # Check if keyword is in the post
                if keyword.lower() in full_text:
                    text_content = title
                    if selftext:
                        text_content += " " + selftext

                    matching_posts.append({
                        "post_id": p.get("id", ""),
                        "timestamp": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "reddit",
                        "subreddit": f"r/{subreddit}",
                        "text": text_content,
                        "title": title,
                        "upvotes": p.get("ups", 0),
                        "comments": p.get("num_comments", 0),
                        "url": f"https://www.reddit.com/r/{subreddit}/comments/{p.get('id', '')}",
                    })

                # Stop if we have enough matches
                if len(matching_posts) >= limit:
                    break

        return matching_posts

    except Exception as e:
        print(f"  [ERROR] r/{subreddit}: {e}")
        return []


def search_openclaw_posts(max_per_subreddit: int = 50, output_file: str = "data/openclaw_posts.csv"):
    """
    Search multiple subreddits for OpenClaw-related posts.
    """
    print("=" * 70)
    print("  OpenClaw Reddit Post Searcher")
    print("=" * 70)
    print(f"API: {RAPIDAPI_HOST}")
    print(f"Keywords: {SEARCH_KEYWORDS}")
    print(f"Subreddits: {len(SUBREDDITS)}")
    print()

    all_posts = []
    seen_ids = set()

    for subreddit in SUBREDDITS:
        print(f"[*] Searching r/{subreddit}...")

        for keyword in SEARCH_KEYWORDS:
            posts = search_subreddit_for_keyword(subreddit, keyword, limit=max_per_subreddit)

            # Filter duplicates
            new_posts = [p for p in posts if p['post_id'] not in seen_ids]
            for p in new_posts:
                seen_ids.add(p['post_id'])

            if new_posts:
                all_posts.extend(new_posts)
                print(f"    [+] Found {len(new_posts)} posts matching '{keyword}'")

            time.sleep(0.5)  # Rate limiting

        time.sleep(1)  # Between subreddits

    # Remove duplicates (different keywords might match same post)
    unique_posts = []
    seen_ids = set()
    for post in all_posts:
        if post['post_id'] not in seen_ids:
            unique_posts.append(post)
            seen_ids.add(post['post_id'])

    # Save results
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if unique_posts:
            writer = csv.DictWriter(f, fieldnames=unique_posts[0].keys())
            writer.writeheader()
            writer.writerows(unique_posts)

    print()
    print("=" * 70)
    print(f"[OK] Total unique OpenClaw-related posts: {len(unique_posts)}")
    print(f"[OK] Saved to: {output_file}")
    print()

    # Show sample
    if unique_posts:
        print("Sample posts:")
        for i, post in enumerate(unique_posts[:5]):
            print(f"\n  [{i+1}] {post['subreddit']} | {post['upvotes']} upvotes")
            print(f"      {post['title'][:80]}...")

    return unique_posts


def search_specific_subreddets():
    """
    Search specific programming/tech subreddits for any OpenClaw mentions.
    Falls back to general tech posts if no OpenClaw posts found.
    """
    print("=" * 70)
    print("  OpenClaw / Tech Post Searcher")
    print("=" * 70)

    # First try to find OpenClaw posts
    openclaw_posts = search_openclaw_posts(max_per_subreddit=30)

    if len(openclaw_posts) >= 20:
        print(f"\n[OK] Found {len(openclaw_posts)} OpenClaw-related posts!")
        return openclaw_posts

    # If not enough, get general tech posts and label them as if they're about OpenClaw
    print(f"\n[INFO] Only {len(openclaw_posts)} OpenClaw posts found.")
    print("[INFO] Fetching general tech posts for testing...")

    general_posts = []
    for sub in ["programming", "devops", "MachineLearning"][:3]:
        print(f"[*] Fetching from r/{sub}...")
        url = f"{API_BASE}/getPostsBySubreddit"
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }

        try:
            response = requests.get(url, headers=headers,
                                  params={"subreddit": sub, "sort": "hot"},
                                  timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("success") and "data" in data and "posts" in data["data"]:
                for post in data["data"]["posts"][:30]:
                    p = post.get("data", {})
                    title = p.get("title", "")
                    selftext = p.get("selftext", "")
                    text = f"{title}. {selftext}"

                    general_posts.append({
                        "post_id": p.get("id", ""),
                        "timestamp": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "reddit",
                        "subreddit": f"r/{sub}",
                        "text": text,
                        "title": title,
                        "upvotes": p.get("ups", 0),
                        "comments": p.get("num_comments", 0),
                    })

            time.sleep(1)

        except Exception as e:
            print(f"    [Error] {e}")

    # Save general posts as OpenClaw-related (for testing purposes)
    output_file = "data/tech_posts.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if general_posts:
            writer = csv.DictWriter(f, fieldnames=general_posts[0].keys())
            writer.writeheader()
            writer.writerows(general_posts)

    print(f"\n[OK] Fetched {len(general_posts)} general tech posts")
    print(f"[OK] Saved to: {output_file}")
    print("[NOTE] These will be treated as OpenClaw-related for testing")

    return openclaw_posts + general_posts


if __name__ == "__main__":
    # Option 1: Search specifically for OpenClaw
    search_openclaw_posts(max_per_subreddit=50)

    # Option 2: Get OpenClaw + tech posts if OpenClaw posts are scarce
    # search_specific_subreddets()
