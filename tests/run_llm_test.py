"""
LLM vs PySpark Classification Comparison
Runs real comparison with Zhipu GLM-4 API
"""
import os
import json
import csv
import time
from datetime import datetime
import requests

# Load API key
from dotenv import load_dotenv
load_dotenv()

ZHIPU_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

LABEL_NAMES = {
    0: "Security Risk",
    1: "Productivity Gain",
    2: "Neutral"
}

CLASSIFICATION_PROMPT = """Classify the text into ONE of these categories:

0 - Security Risk: security vulnerabilities, API leaks, data breaches, hacks, exploits, attacks
1 - Productivity Gain: efficiency improvements, automation, time savings, workflow optimization
2 - Neutral: general discussion, questions, technical sharing (not security or productivity)

Return ONLY a single digit (0, 1, or 2).

Text: {text}

Answer:"""


def classify_with_glm(text: str) -> int:
    """Classify text using GLM-4"""

    if not ZHIPU_API_KEY:
        print("    [!] No API key configured")
        return -1

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZHIPU_API_KEY}"
    }

    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": CLASSIFICATION_PROMPT.format(text=text[:600])}],
        "temperature": 0.1,
        "max_tokens": 10
    }

    try:
        response = requests.post(ZHIPU_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()

        content = result["choices"][0]["message"]["content"].strip()

        # Extract digit
        for char in content:
            if char in "012":
                return int(char)

        return -2  # Parse error

    except Exception as e:
        print(f"    [!] API Error: {str(e)[:50]}")
        return -3


def classify_with_keywords(text: str) -> int:
    """Simple keyword-based classification"""

    text_lower = text.lower()

    security_kws = ['security', 'vulnerability', 'exploit', 'breach', 'hack',
                    'injection', 'compromised', 'attack', 'malware', 'threat']

    productivity_kws = ['productivity', 'efficient', 'automat', 'faster',
                        'workflow', 'streamline', 'optim', 'saves time']

    sec_score = sum(1 for kw in security_kws if kw in text_lower)
    prod_score = sum(1 for kw in productivity_kws if kw in text_lower)

    if sec_score >= 1:
        return 0
    elif prod_score >= 1:
        return 1
    else:
        return 2


def main():
    print("=" * 70)
    print("  LLM (GLM-4) vs Keyword Classification Comparison")
    print("=" * 70)
    print()

    if not ZHIPU_API_KEY:
        print("[!] ZHIPUAI_API_KEY not found in .env file")
        print("    Please add: ZHIPUAI_API_KEY=your_key_here")
        return

    print(f"[+] API Key configured: {ZHIPU_API_KEY[:10]}...")
    print()

    # Load data
    posts = []
    with open('data/reddit_real_posts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append({
                'post_id': row['post_id'],
                'subreddit': row['subreddit'],
                'text': row['text'],
                'upvotes': int(row['upvotes']),
            })

    num_samples = 15
    sample_posts = posts[:num_samples]

    print(f"[*] Testing {len(sample_posts)} real Reddit posts")
    print()

    results = []

    for i, post in enumerate(sample_posts):
        print(f"[{i+1}/{len(sample_posts)}] {post['subreddit']} | {post['upvotes']} upvotes")
        print(f"    Text: {post['text'][:70]}...")

        # Keyword classification
        kw_pred = classify_with_keywords(post['text'])

        # GLM classification
        print(f"    [*] GLM-4 classifying...", end="", flush=True)
        glm_pred = classify_with_glm(post['text'])

        if glm_pred >= 0:
            print(f" {LABEL_NAMES[glm_pred]}")
            agreement = (kw_pred == glm_pred)
            status = "MATCH" if agreement else "DIFFER"
        else:
            status = "ERROR"

        print(f"    Keyword: {LABEL_NAMES[kw_pred]} | GLM: {LABEL_NAMES.get(glm_pred, '?')} | {status}")
        print()

        results.append({
            'post_id': post['post_id'],
            'subreddit': post['subreddit'],
            'text_preview': post['text'][:80],
            'keyword_pred': kw_pred,
            'glm_pred': glm_pred,
            'agreement': (kw_pred == glm_pred) if glm_pred >= 0 else None
        })

        time.sleep(0.3)

    # Statistics
    valid = [r for r in results if r['glm_pred'] >= 0]

    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)

    if valid:
        agreements = sum(1 for r in valid if r['agreement'])
        agreement_rate = agreements / len(valid) * 100

        print(f"\nValid comparisons: {len(valid)}")
        print(f"Agreements: {agreements} ({agreement_rate:.1f}%)")
        print(f"Disagreements: {len(valid) - agreements}")

        print("\nDistribution:")
        print(f"{'Category':<20} {'Keyword':<10} {'GLM':<10}")
        print("-" * 40)
        for label in [0, 1, 2]:
            kw_c = sum(1 for r in valid if r['keyword_pred'] == label)
            glm_c = sum(1 for r in valid if r['glm_pred'] == label)
            print(f"{LABEL_NAMES[label]:<20} {kw_c:<10} {glm_c:<10}")

        # Disagreements
        diff = [r for r in valid if not r['agreement']]
        if diff:
            print(f"\nDisagreements ({len(diff)}):")
            for r in diff[:5]:
                print(f"\n  [{r['subreddit']}]")
                print(f"  {r['text_preview']}...")
                print(f"  Keyword: {LABEL_NAMES[r['keyword_pred']]} | GLM: {LABEL_NAMES[r['glm_pred']]}")

    # Save results
    os.makedirs("benchmark-results", exist_ok=True)
    output = f"benchmark-results/glm_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_samples": len(sample_posts),
            "valid_comparisons": len(valid),
            "agreements": agreements if valid else 0,
            "agreement_rate_pct": agreement_rate if valid else 0,
            "results": valid
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Results saved: {output}")


if __name__ == "__main__":
    main()
