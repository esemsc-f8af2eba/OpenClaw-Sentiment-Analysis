"""
Search for OpenClaw posts using RapidAPI Search endpoint
"""
import requests
import csv
import time
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "reddit34.p.rapidapi.com")
API_BASE = f"https://{RAPIDAPI_HOST}"


def search_openclaw_posts():
    """Search for posts containing OpenClaw"""

    # Try search endpoint
    url = f"{API_BASE}/getSearchPosts"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    search_queries = [
        "OpenClaw",
        "OpenClaw tool",
        "OpenClaw AI",
        "OpenClaw automation"
    ]

    all_posts = []
    seen_ids = set()

    print("=" * 60)
    print("  Searching OpenClaw Posts")
    print("=" * 60)

    for query in search_queries:
        print(f"\n[*] Searching for: {query}")

        params = {"q": query}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("success") and "data" in data:
                posts = data["data"].get("posts", [])

                for post in posts:
                    p = post.get("data", {})
                    post_id = p.get("id", "")

                    if post_id not in seen_ids:
                        seen_ids.add(post_id)

                        title = p.get("title", "")
                        selftext = p.get("selftext", "")
                        text = f"{title}\n{selftext}" if selftext else title

                        all_posts.append({
                            "post_id": post_id,
                            "timestamp": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                            "source": "reddit",
                            "subreddit": f"r/{p.get('subreddit', '')}",
                            "text": text,
                            "title": title,
                            "upvotes": p.get("ups", 0),
                            "comments": p.get("num_comments", 0),
                            "url": f"https://www.reddit.com{p.get('permalink', '')}",
                        })

                print(f"    [+] Found {len(posts)} posts")

            time.sleep(2)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"    [!] Rate limited - skipping")
            else:
                print(f"    [!] Error: {e}")
        except Exception as e:
            print(f"    [!] Error: {e}")

    # Save results
    if all_posts:
        output_file = "data/openclaw_search_results.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_posts[0].keys())
            writer.writeheader()
            writer.writerows(all_posts)

        print()
        print(f"[OK] Total posts: {len(all_posts)}")
        print(f"[OK] Saved: {output_file}")

        # Show sample
        print("\nSample posts:")
        for p in all_posts[:5]:
            print(f"\n  [{p['subreddit']}] {p['upvotes']} upvotes")
            print(f"  {p['title'][:70]}")
            print(f"  URL: {p['url']}")
    else:
        print("\n[!] No posts found")

    return all_posts


if __name__ == "__main__":
    search_openclaw_posts()
