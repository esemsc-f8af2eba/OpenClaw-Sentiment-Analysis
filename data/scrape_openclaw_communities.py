"""
Reddit Scraper - OpenClaw Specific Communities
Scrapes posts from OpenClaw-related subreddits
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

# OpenClaw-specific subreddits
OPENCLAW_SUBREDDITS = [
    "OpenClaw",
    "OpenClawUseCases",
    "OpenClawCentral",
    "OpenclawBot",
    "openclaw"  # lowercase variant
]


def scrape_subreddit_posts(subreddit: str, limit: int = 100) -> list:
    """
    Scrape posts from a specific subreddit.
    """
    url = f"{API_BASE}/getPostsBySubreddit"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    # Try different sort options to get more posts
    sort_options = ["hot", "new", "top"]

    all_posts = []

    for sort in sort_options:
        if len(all_posts) >= limit:
            break

        params = {"subreddit": subreddit, "sort": sort}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("success") and "data" in data and "posts" in data["data"]:
                posts = data["data"]["posts"]

                for post in posts:
                    p = post.get("data", {})
                    post_id = p.get("id", "")

                    # Avoid duplicates
                    if any(existing['post_id'] == post_id for existing in all_posts):
                        continue

                    title = p.get("title", "")
                    selftext = p.get("selftext", "")
                    text_content = title
                    if selftext and selftext.strip():
                        text_content += "\n" + selftext

                    all_posts.append({
                        "post_id": post_id,
                        "timestamp": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "reddit",
                        "subreddit": f"r/{subreddit}",
                        "text": text_content,
                        "title": title,
                        "selftext": selftext,
                        "upvotes": p.get("ups", 0),
                        "downvotes": p.get("downs", 0),
                        "score": p.get("score", 0),
                        "comments": p.get("num_comments", 0),
                        "author": p.get("author", ""),
                        "permalink": f"https://www.reddit.com/r/{subreddit}/comments/{post_id}",
                    })

                print(f"    [{sort}] Got {len(posts)} posts")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"    [!] Subreddit r/{subreddit} not found (404)")
                return []
            elif e.response.status_code == 429:
                print(f"    [!] Rate limited, waiting...")
                time.sleep(5)
            else:
                print(f"    [!] HTTP Error: {e}")
        except Exception as e:
            print(f"    [!] Error: {e}")

        time.sleep(1)

    return all_posts[:limit]


def main():
    print("=" * 70)
    print("  OpenClaw Communities Scraper")
    print("=" * 70)
    print(f"Target Subreddits: {OPENCLAW_SUBREDDITS}")
    print(f"API: {RAPIDAPI_HOST}")
    print()

    all_posts = []
    seen_ids = set()

    for subreddit in OPENCLAW_SUBREDDITS:
        print(f"[*] Scraping r/{subreddit}...")

        posts = scrape_subreddit_posts(subreddit, limit=100)

        if posts:
            # Filter duplicates
            new_posts = [p for p in posts if p['post_id'] not in seen_ids]
            for p in new_posts:
                seen_ids.add(p['post_id'])

            all_posts.extend(new_posts)
            print(f"    [OK] Got {len(new_posts)} unique posts from r/{subreddit}")
        else:
            print(f"    [--] No posts from r/{subreddit}")

        time.sleep(2)

    # Save results
    output_file = "data/openclaw_community_posts.csv"
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    if all_posts:
        # Sort by upvotes
        all_posts.sort(key=lambda x: x['upvotes'], reverse=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_posts[0].keys())
            writer.writeheader()
            writer.writerows(all_posts)

        print()
        print("=" * 70)
        print(f"[OK] Total unique posts: {len(all_posts)}")
        print(f"[OK] Saved to: {output_file}")
        print()

        # Show stats by subreddit
        from collections import Counter
        sub_counts = Counter(p['subreddit'] for p in all_posts)
        print("Posts by subreddit:")
        for sub, count in sub_counts.most_common():
            print(f"  {sub}: {count}")

        print()
        print("Top posts by upvotes:")
        for i, post in enumerate(all_posts[:5]):
            print(f"\n  [{i+1}] {post['subreddit']} | {post['upvotes']} upvotes | {post['comments']} comments")
            print(f"      Title: {post['title'][:80]}")
            print(f"      URL: {post['permalink']}")

        # Show some sample content
        print()
        print("Sample post content:")
        for post in all_posts[:3]:
            print(f"\n  [{post['subreddit']}]")
            print(f"  {post['text'][:200]}...")

    else:
        print()
        print("[WARNING] No posts found!")
        print("This could mean:")
        print("  - The subreddits don't exist")
        print("  - They are private/restricted")
        print("  - API rate limiting occurred")

    return all_posts


if __name__ == "__main__":
    main()
