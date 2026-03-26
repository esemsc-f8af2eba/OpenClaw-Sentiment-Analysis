"""
test_reddit_official.py
Test official Reddit API connection using PRAW.
"""
import praw
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, REDDIT_SUBREDDITS, REDDIT_SEARCH_QUERY

def test_official_reddit_api():
    """Test official Reddit API connection."""

    print("Testing Official Reddit API (PRAW)...")
    print()

    if not REDDIT_CLIENT_ID or REDDIT_CLIENT_ID == "your_client_id_here":
        print("[ERROR] Reddit API credentials not set!")
        print("\nTo get credentials:")
        print("  1. Go to https://www.reddit.com/prefs/apps")
        print("  2. Click 'create app' or 'create another app'")
        print("  3. Select 'script'")
        print("  4. Fill in:")
        print("     - name: openclaw-sentiment")
        print("     - description: OpenClaw Sentiment Analysis")
        print("     - about url: https://github.com/yourusername/openclaw")
        print("     - redirect uri: http://localhost:8080")
        print("  5. Copy the client_id (under the app name)")
        print("  6. Copy the client_secret")
        print("\n  Then add to .env file:")
        print("     REDDIT_CLIENT_ID=your_client_id")
        print("     REDDIT_CLIENT_SECRET=your_client_secret")
        return False

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        print(f"Connected to Reddit as user: {reddit.user.me()}")

        # Test search
        print(f"\nSearching for '{REDDIT_SEARCH_QUERY}' in r/{REDDIT_SUBREDDITS[0]}...")

        subreddit = reddit.subreddit(REDDIT_SUBREDDITS[0])
        results = list(subreddit.search(REDDIT_SEARCH_QUERY, limit=3))

        if results:
            print(f"\n[OK] Found {len(results)} posts:\n")
            for i, post in enumerate(results, 1):
                print(f"  [{i}] {post.title[:60]}...")
                print(f"      Upvotes: {post.score}")
                print(f"      Comments: {post.num_comments}")
                print(f"      URL: {post.url[:50]}...")
                print()

            print(f"[SUCCESS] Official Reddit API is working!")
            return True
        else:
            print(f"[WARNING] No results found for '{REDDIT_SEARCH_QUERY}'")
            return True  # Connection worked, just no results

    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nTroubleshooting:")
        print("  1. Verify your client_id and client_secret are correct")
        print("  2. Make sure you copied the entire values (no extra spaces)")
        print("  3. Check that your app type is 'script'")
        return False


if __name__ == "__main__":
    success = test_official_reddit_api()

    if success:
        print("\nNext steps:")
        print("  - Run: python data/reddit_scraper.py")
        print("  - This will collect posts and save to data/reddit_posts.csv")
