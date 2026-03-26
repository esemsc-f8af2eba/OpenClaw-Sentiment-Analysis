"""
clean_scraped_data.py
Data cleaning pipeline for scraped Reddit posts.
Extracts and standardizes fields, filters low-quality content.
"""
import pandas as pd
import re
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def extract_post_type(title: str) -> str:
    """Extract post type from title tags like [P], [D], [R]."""
    if not title or pd.isna(title):
        return "Unknown"

    match = re.search(r'\[([A-Za-z]+)\]', title)
    if match:
        return match.group(1)

    # Try common patterns
    tags = {
        "[P]": "Project",
        "[D]": "Discussion",
        "[R]": "Research",
        "[Q]": "Question",
        "[N]": "News",
        "[I]": "Issue",
        "[Tutorial]": "Tutorial",
    }

    for tag, type_name in tags.items():
        if tag in title:
            return type_name

    return "Unknown"


def is_high_quality_post(row: pd.Series) -> bool:
    """
    Filter criteria for high-quality posts:
    - Minimum text length (after removing tags)
    - Not just a title (has content)
    - Not obviously spam
    """
    text = row.get("text", "")
    if pd.isna(text) or not text:
        return False

    # Remove post type tags for length check
    clean_text = re.sub(r'\[.*?\]', '', text).strip()

    # Minimum length (shorter posts are often low quality)
    if len(clean_text) < 30:
        return False

    # Check for obvious spam patterns
    spam_patterns = [
        r'buy now',
        r'click here',
        r'free.*bitcoin',
        r'make money fast',
        r'check my profile',
    ]

    for pattern in spam_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    return True


def clean_data(
    input_path: str = "data/reddit_posts.csv",
    output_path: str = "data/reddit_posts_cleaned.csv"
) -> pd.DataFrame:
    """
    Clean and standardize scraped Reddit data.

    Extracts:
    - user_id: Author username
    - post_id: Unique post identifier
    - title: Post title
    - content: Full content (title + body)
    - source_subreddit: Which subreddit
    - post_type: [P], [D], [R], etc.
    - timestamp: Standardized datetime
    - engagement: upvotes, comments
    """
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"  Original rows: {len(df)}")

    # --- 1. Extract post type from title ---
    if "title" in df.columns:
        df["post_type"] = df["title"].apply(extract_post_type)
    else:
        df["post_type"] = df["text"].apply(extract_post_type)

    # --- 2. Split title and content ---
    if "title" in df.columns:
        df["title_clean"] = df["title"]
    else:
        # First line is usually the title
        df["title_clean"] = df["text"].apply(lambda x: str(x).split('\n')[0] if x else "")

    if "selftext" in df.columns:
        df["content"] = df["text"]
    else:
        df["content"] = df["text"]  # Keep full text for now

    # --- 3. Add metadata ---
    # Use author field if available, otherwise unknown
    if "author" in df.columns:
        df["user_id"] = df["author"].fillna("unknown")
    else:
        df["user_id"] = "unknown"
    df["source_category"] = "reddit"

    # --- 4. Standardize timestamp ---
    df["timestamp_iso"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    # --- 5. Filter low-quality posts ---
    print("\nApplying quality filters...")
    before_filter = len(df)
    df = df[df.apply(is_high_quality_post, axis=1)]
    filtered_out = before_filter - len(df)
    print(f"  Filtered out: {filtered_out} low-quality posts ({filtered_out/before_filter*100:.1f}%)")

    # --- 6. Remove duplicates (by post_id) ---
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["post_id"], keep="first")
    duplicates_removed = before_dedup - len(df)
    print(f"  Removed duplicates: {duplicates_removed}")

    # --- 7. Select and order columns ---
    columns_to_include = {
        "post_id": df["post_id"],
        "user_id": df["user_id"],
        "title": df["title_clean"],
        "content": df["content"],
        "post_type": df["post_type"],
        "source": df["source"],
        "source_subreddit": df["subreddit"],
        "source_category": df["source_category"],
        "timestamp": df["timestamp_iso"],
        "upvotes": df["upvotes"],
        "comments": df["comments"],
    }

    # Add optional fields if available
    optional_fields = ["downs", "score", "link_flair", "permalink"]
    for field in optional_fields:
        if field in df.columns:
            columns_to_include[field] = df[field]

    result_df = pd.DataFrame(columns_to_include)

    # --- 8. Save ---
    result_df.to_csv(output_path, index=False)
    print(f"\n[OK] Saved {len(result_df)} cleaned posts to {output_path}")

    # --- 9. Summary ---
    print("\n=== Summary ===")
    print(f"Total posts: {len(result_df)}")
    print(f"\nPost type distribution:")
    print(result_df["post_type"].value_counts())
    print(f"\nSubreddit distribution:")
    print(result_df["source_subreddit"].value_counts())
    print(f"\nContent length stats:")
    result_df["content_length"] = result_df["content"].str.len()
    print(result_df["content_length"].describe())

    return result_df


def update_scraper_with_author():
    """
    Note: To capture author field, update reddit_scraper_rapidapi.py
    to include the 'author' field in the data dictionary.
    """
    print("\n[INFO] To capture author field, update the scraper:")
    print("  In reddit_scraper_rapidapi.py, line ~70:")
    print("  Add: 'author': p.get('author', 'unknown'),")
    print("  And update this cleaning script to use it.")


if __name__ == "__main__":
    # Run the cleaning pipeline
    cleaned_df = clean_data()

    # Show sample
    print("\n=== Sample Cleaned Posts ===")
    for idx, row in cleaned_df.head(5).iterrows():
        print(f"\n[{row['post_type']}] {row['source_subreddit']}")
        print(f"  Title: {row['title'][:60]}...")
        print(f"  User: {row['user_id']}")
        print(f"  Time: {row['timestamp']}")
        print(f"  Engagement: {row['upvotes']} upvotes, {row['comments']} comments")

    update_scraper_with_author()
