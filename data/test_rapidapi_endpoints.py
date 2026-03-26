"""
test_rapidapi_endpoints.py
Test various RapidAPI Reddit endpoints to find a working one.
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# Common RapidAPI Reddit providers and their endpoints
PROVIDERS = {
    "reddit34": "reddit34.p.rapidapi.com",
    "apidojo": "apidojo-hacker-news-v1.p.rapidapi.com",  # Alternative
    "social": "social-api2.p.rapidapi.com",  # Alternative
}

# Various endpoints to try for Reddit
ENDPOINTS_TO_TRY = {
    "reddit34": [
        "/search",
        "/search/posts",
        "/v1/search",
        "/submissions",
        "/subreddit/MachineLearning/hot",
        "/r/MachineLearning/hot",
        "/posts",
        "/subreddit/search",
        "/searchSubreddit",
        "/getSubredditPosts",
        "/get_posts",
    ],
    "social": [
        "/reddit/posts",
        "/reddit/search",
        "/v1/reddit/posts",
    ]
}


def test_provider(provider_name: str, host: str, endpoints: list):
    """Test a specific provider with its endpoints."""
    print(f"\n{'='*60}")
    print(f"Testing provider: {provider_name} ({host})")
    print(f"{'='*60}")

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": host
    }

    for endpoint in endpoints:
        url = f"https://{host}{endpoint}"
        print(f"\n  Trying: {url}")

        # Try different query parameters
        params_list = [
            {"q": "test", "limit": 5},
            {"query": "test", "limit": 5},
            {"subreddit": "MachineLearning", "limit": 5},
            {"sub": "MachineLearning", "limit": 5},
        ]

        for params in params_list:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    print(f"    [✅ SUCCESS] Status: 200")
                    print(f"    Params used: {params}")
                    data = response.json()
                    print(f"    Response type: {type(data)}")
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]
                        print(f"    Top keys: {keys}")
                    return host, endpoint, params, data
                elif response.status_code == 401:
                    print(f"    [❌] Invalid API key")
                    return None, None, None, None
                elif response.status_code == 403:
                    print(f"    [❌] Forbidden - check subscription")
                    return None, None, None, None
                elif response.status_code == 429:
                    print(f"    [⚠️] Rate limited - too many requests")
                elif response.status_code not in [404, 400]:
                    print(f"    [?] Status: {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"    [⏱️] Timeout")
            except Exception as e:
                print(f"    [❌] Error: {str(e)[:50]}")

    return None, None, None, None


def main():
    print(f"API Key: {RAPIDAPI_KEY[:10]}...{RAPIDAPI_KEY[-4:] if RAPIDAPI_KEY else 'None'}")

    for provider_name, host in PROVIDERS.items():
        endpoints = ENDPOINTS_TO_TRY.get(provider_name, [])
        if not endpoints:
            print(f"\nSkipping {provider_name} - no endpoints defined")
            continue

        host, endpoint, params, data = test_provider(provider_name, host, endpoints)

        if host and endpoint and data:
            print(f"\n{'='*60}")
            print(f"[✅] FOUND WORKING API!")
            print(f"{'='*60}")
            print(f"Provider: {provider_name}")
            print(f"Host: {host}")
            print(f"Endpoint: {endpoint}")
            print(f"Params: {params}")
            print(f"\nSample response:")
            print(str(data)[:500])

            # Save to config suggestion
            print(f"\n{'='*60}")
            print("To use this API, update your .env file:")
            print(f"RAPIDAPI_HOST={host}")
            print(f"# And update the endpoint in your scraper")
            return

    print(f"\n{'='*60}")
    print("[❌] No working endpoint found")
    print(f"{'='*60}")
    print("\nSuggestions:")
    print("1. Check https://rapidapi.com/hub for Reddit APIs")
    print("2. Make sure you've subscribed to the correct API")
    print("3. Check your API key and available requests")


if __name__ == "__main__":
    main()
