"""
test_reddit_api.py
Test your Reddit RapidAPI connection - tries multiple endpoints.
"""
import requests
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import RAPIDAPI_KEY, RAPIDAPI_HOST

def test_endpoints():
    """Test multiple possible endpoints."""

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    # Common endpoints to try
    endpoints = [
        ("/search", {"query": "test", "limit": 1}),
        ("/v1/search", {"q": "test", "limit": 1}),
        ("/submissions", {"subreddit": "all", "limit": 1}),
        ("/r/MachineLearning/hot", {"limit": 1}),
    ]

    print(f"Testing Reddit RapidAPI: {RAPIDAPI_HOST}")
    print(f"API Key: {RAPIDAPI_KEY[:10]}...{RAPIDAPI_KEY[-4:]}")
    print()

    for endpoint, params in endpoints:
        url = f"https://{RAPIDAPI_HOST}{endpoint}"
        print(f"Trying: {url}")

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"  [OK] This endpoint works!")
                print(f"  Response sample: {str(data)[:200]}...")
                return url, params
            elif response.status_code == 401:
                print(f"  [ERROR] Invalid API key!")
                return None, None
            elif response.status_code == 403:
                print(f"  [ERROR] Forbidden - check API key permissions")
                return None, None
            else:
                print(f"  Response: {response.text[:100]}...")

        except Exception as e:
            print(f"  Error: {e}")

        print()

    print("\n[FAILED] Could not find a working endpoint.")
    print("\nPlease check:")
    print("  1. https://rapidapi.com/reddit34-reddit34-default/api/reddit-scraper")
    print("  2. Your API key is valid")
    print("  3. You have available requests")
    return None, None


if __name__ == "__main__":
    url, params = test_endpoints()

    if url:
        print(f"\n[SUCCESS] Working endpoint found:")
        print(f"  URL: {url}")
        print(f"  Params: {params}")
    else:
        print("\n[INFO] To use the official Reddit API instead:")
        print("  1. Go to https://www.reddit.com/prefs/apps")
        print("  2. Create an app (script type)")
        print("  3. Copy client_id and client_secret")
        print("  4. Add to .env file:")
        print("     REDDIT_CLIENT_ID=your_client_id")
        print("     REDDIT_CLIENT_SECRET=your_client_secret")
