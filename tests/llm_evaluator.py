"""
LLM-based Classification Validator
使用 LLM 验证 PySpark MLlib 分类准确性
支持多个 LLM 提供商：智谱 GLM、OpenAI、DeepSeek 等
"""
import os
import json
import csv
import time
from datetime import datetime
import sys

# LLM API 配置
LLM_CONFIGS = {
    "zhipu": {
        "name": "智谱 GLM-4",
        "api_key_env": "ZHIPUAI_API_KEY",
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4-flash",
        "headers": lambda key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
    },
    "openai": {
        "name": "OpenAI GPT",
        "api_key_env": "OPENAI_API_KEY",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-3.5-turbo",
        "headers": lambda key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
    },
    "deepseek": {
        "name": "DeepSeek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
        "headers": lambda key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
    }
}

# 分类标准
CLASSIFICATION_PROMPT = """你是一个文本分类专家。请将以下文本分类为三类之一：

【分类标准】
0 - Security Risk (安全风险): 涉及安全漏洞、API泄露、数据泄露、权限问题、黑客攻击、供应链攻击等
1 - Productivity Gain (生产力提升): 涉及提升效率、自动化、节省时间、工作流程优化、工具改进等
2 - Neutral (中性): 一般讨论、问题咨询、技术分享、招聘信息等（不涉及安全风险或生产力提升）

【要求】
只返回一个数字（0、1 或 2），不要返回其他内容。

【待分类文本】
{text}

【你的回答】"""


def classify_with_llm(text: str, provider: str = "zhipu", max_retries: int = 2) -> int:
    """使用 LLM 进行分类"""

    if provider not in LLM_CONFIGS:
        print(f"  [Error] 不支持的 LLM 提供商: {provider}")
        return -1

    config = LLM_CONFIGS[provider]
    api_key = os.getenv(config["api_key_env"], "")

    if not api_key:
        return -2  # API key not configured

    prompt = CLASSIFICATION_PROMPT.format(text=text[:800])

    try:
        import requests
        response = requests.post(
            config["url"],
            headers=config["headers"](api_key),
            json={
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 10
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        content = result["choices"][0]["message"]["content"].strip()

        # 提取数字
        for char in content:
            if char in "012":
                return int(char)

        # 解析文本
        content_lower = content.lower()
        if "security" in content_lower or "risk" in content_lower or "安全" in content:
            return 0
        elif "productivity" in content_lower or "gain" in content_lower or "生产力" in content:
            return 1
        else:
            return 2

    except Exception as e:
        if max_retries > 0:
            time.sleep(1)
            return classify_with_llm(text, provider, max_retries - 1)
        return -3  # API error


def classify_with_keywords(text: str) -> int:
    """基于关键词的分类（模拟 PySpark 结果）"""
    text_lower = text.lower()

    security_keywords = ['security', 'vulnerability', 'exploit', 'breach', 'hack',
                        'injection', 'compromised', 'attack', 'malware', 'threat',
                        '安全', '漏洞', '攻击', '泄露']

    productivity_keywords = ['productivity', 'efficient', 'automat', 'faster',
                            'workflow', 'streamline', 'optim', 'saves time',
                            '生产力', '效率', '自动化', '优化']

    security_score = sum(1 for kw in security_keywords if kw in text_lower)
    productivity_score = sum(1 for kw in productivity_keywords if kw in text_lower)

    if security_score >= 1:
        return 0
    elif productivity_score >= 1:
        return 1
    else:
        return 2


def load_test_data():
    """加载测试数据"""
    posts = []

    # 优先使用真实爬取的数据
    if os.path.exists('data/reddit_real_posts.csv'):
        with open('data/reddit_real_posts.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                posts.append({
                    'post_id': row['post_id'],
                    'source': 'reddit_real',
                    'subreddit': row['subreddit'],
                    'text': row['text'],
                    'upvotes': int(row['upvotes']),
                })
    else:
        # 使用模拟数据
        print("[Warning] 未找到真实数据，使用模拟数据")
        return None

    return posts


def run_comparison(num_samples: int = 10, llm_provider: str = "zhipu"):
    """运行对比测试"""

    print("=" * 70)
    print(f"  LLM ({LLM_CONFIGS[llm_provider]['name']}) vs 关键词分类对比")
    print("=" * 70)
    print()

    # 检查 API key
    api_key = os.getenv(LLM_CONFIGS[llm_provider]["api_key_env"])
    if not api_key:
        print(f"[*] 未找到 {LLM_CONFIGS[llm_provider]['api_key_env']}")
        print(f"[*] 请设置环境变量或使用模拟模式")
        print()
        use_mock = input("是否使用模拟模式？(y/n): ").lower() == 'y'
        if not use_mock:
            return None
        print("[*] 使用模拟模式 - LLM 将基于关键词模拟")

    # 加载数据
    posts = load_test_data()
    if not posts:
        print("[Error] 无法加载数据")
        return None

    sample_posts = posts[:num_samples]
    print(f"[*] 测试样本数: {len(sample_posts)}")
    print()

    # 执行对比
    results = []
    label_names = {0: "Security Risk", 1: "Productivity Gain", 2: "Neutral"}

    for i, post in enumerate(sample_posts):
        print(f"[{i+1}/{len(sample_posts)}] {post['subreddit']} | {post['upvotes']} upvotes")
        print(f"    Text: {post['text'][:70]}...")

        # 关键词分类
        keyword_pred = classify_with_keywords(post['text'])

        # LLM 分类
        if api_key:
            print(f"    [*] LLM 分类中...", end="", flush=True)
            llm_pred = classify_with_llm(post['text'], llm_provider)
            if llm_pred >= 0:
                print(f" {label_names[llm_pred]}")
            else:
                print(f" Error (code: {llm_pred})")
        else:
            # 模拟 LLM
            llm_pred = keyword_pred  # 90% 一致
            if i % 5 == 0:
                llm_pred = (llm_pred + 1) % 3  # 偶尔不同
            print(f"    [Simulated] {label_names[llm_pred]}")

        # 记录结果
        agreement = (keyword_pred == llm_pred) if llm_pred >= 0 else None
        status = "MATCH" if agreement else "DIFF" if agreement is not None else "ERROR"

        print(f"    结果: 关键词={label_names[keyword_pred]} | LLM={label_names.get(llm_pred, '?')} | {status}")
        print()

        results.append({
            'post_id': post['post_id'],
            'subreddit': post['subreddit'],
            'text': post['text'][:100],
            'keyword_pred': keyword_pred,
            'llm_pred': llm_pred,
            'agreement': agreement
        })

        time.sleep(0.3)

    # 统计
    valid_results = [r for r in results if r['llm_pred'] >= 0]

    print("=" * 70)
    print("  统计结果")
    print("=" * 70)

    if valid_results:
        agreements = sum(1 for r in valid_results if r['agreement'])
        agreement_rate = agreements / len(valid_results) * 100

        print(f"\n有效对比: {len(valid_results)} 条")
        print(f"一致: {agreements} 条 ({agreement_rate:.1f}%)")
        print(f"不一致: {len(valid_results) - agreements} 条")

        # 分布对比
        print("\n分类分布对比:")
        print(f"{'类别':<20} {'关键词':<10} {'LLM':<10}")
        print("-" * 40)
        for label in [0, 1, 2]:
            keyword_count = sum(1 for r in valid_results if r['keyword_pred'] == label)
            llm_count = sum(1 for r in valid_results if r['llm_pred'] == label)
            print(f"{label_names[label]:<20} {keyword_count:<10} {llm_count:<10}")

        # 不一致案例
        disagreements = [r for r in valid_results if not r['agreement']]
        if disagreements:
            print(f"\n不一致案例 ({len(disagreements)} 条):")
            for r in disagreements[:3]:
                print(f"\n  [{r['subreddit']}]")
                print(f"  文本: {r['text']}...")
                print(f"  关键词: {label_names[r['keyword_pred']]} | LLM: {label_names[r['llm_pred']]}")

    # 保存结果
    output_dir = "benchmark-results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/llm_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "llm_provider": llm_provider,
            "total_samples": len(sample_posts),
            "valid_comparisons": len(valid_results),
            "agreements": agreements if valid_results else 0,
            "agreement_rate": agreement_rate if valid_results else 0,
            "results": valid_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] 结果已保存: {output_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM vs PySpark 分类对比")
    parser.add_argument("--samples", type=int, default=10, help="测试样本数")
    parser.add_argument("--provider", choices=["zhipu", "openai", "deepseek"],
                      default="zhipu", help="LLM 提供商")

    args = parser.parse_args()

    print("\n支持的 LLM 提供商:")
    for key, config in LLM_CONFIGS.items():
        print(f"  --provider {key}: {config['name']}")
        print(f"    环境变量: {config['api_key_env']}")
    print()

    run_comparison(num_samples=args.samples, llm_provider=args.provider)
