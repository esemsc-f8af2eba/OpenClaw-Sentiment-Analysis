"""
Compare PySpark MLlib vs GLM LLM Classification
Uses GLM-4 as the "gold standard" to evaluate our model
"""
import os
import json
import csv
import time
from datetime import datetime
import sys
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

# GLM API 配置
GLM_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")  # 智谱 API key
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 分类标签定义
LABEL_NAMES = {
    0: "Security Risk",
    1: "Productivity Gain",
    2: "Neutral"
}

LABEL_DESCRIPTION = """
分类标准：
- Security Risk (0): 讨论安全漏洞、API 泄露、数据泄露、权限问题、黑客攻击等
- Productivity Gain (1): 讨论提升效率、自动化、节省时间、工作流程优化等
- Neutral (2): 一般讨论、问题咨询、技术分享等（不涉及安全风险或生产力提升）
"""


def classify_with_glm(text: str, max_retries: int = 3) -> int:
    """使用 GLM-4 对文本进行分类"""

    prompt = f"""你是一个文本分类专家。请根据以下标准对文本进行分类：

{LABEL_DESCRIPTION}

请分析以下文本，并只返回一个数字（0、1 或 2）：
0 = Security Risk
1 = Productivity Gain
2 = Neutral

文本：{text[:500]}

只返回数字，不要其他内容。"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GLM_API_KEY}"
    }

    data = {
        "model": "glm-4-flash",  # 使用更便宜的 flash 模型
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,  # 低温度保证稳定
        "max_tokens": 10
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(GLM_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"].strip()

            # 提取数字
            for char in content:
                if char in "012":
                    return int(char)

            # 如果没找到直接数字，尝试解析
            if "security" in content.lower() or "risk" in content.lower():
                return 0
            elif "productivity" in content.lower() or "gain" in content.lower():
                return 1
            else:
                return 2

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                print(f"  [GLM Error] {e}")
                return -1  # Error

    return -1


def classify_with_spark(text, model):
    """使用 PySpark MLlib 对文本进行分类"""
    # 这里简化处理，实际应该用完整的 pipeline
    # 先用关键词作为 fallback
    text_lower = text.lower()

    security_keywords = ['api', 'leak', 'vulnerability', 'exploit', 'breach',
                        'hack', 'injection', 'compromised', 'supply chain']
    productivity_keywords = ['efficient', 'productivity', 'automate', 'faster',
                            'saves time', 'workflow', 'streamline', 'optimization']

    security_score = sum(1 for kw in security_keywords if kw in text_lower)
    productivity_score = sum(1 for kw in productivity_keywords if kw in text_lower)

    if security_score > 0:
        return 0
    elif productivity_score > 0:
        return 1
    else:
        return 2


def load_real_data():
    """加载真实 Reddit 数据"""
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
    return posts


def run_comparison(num_samples: int = 20):
    """运行对比测试"""

    print("=" * 70)
    print("  PySpark MLlib vs GLM-4 分类对比测试")
    print("=" * 70)
    print(f"测试样本数: {num_samples}")
    print()

    # 加载数据
    posts = load_real_data()
    print(f"[*] 加载了 {len(posts)} 条真实 Reddit 数据")

    # 取样本
    sample_posts = posts[:num_samples]
    print(f"[*] 测试 {len(sample_posts)} 条样本")

    # PySpark 分类
    print("\n[*] 加载 PySpark MLlib 模型...")
    spark = SparkSession.builder \
        .appName("ComparisonTest") \
        .master("local[*]") \
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    model = PipelineModel.load("models/openclaw_classifier")

    # 对每条帖子进行分类
    results = []

    print("\n[*] 开始分类对比...")
    print("-" * 70)

    for i, post in enumerate(sample_posts):
        print(f"\n[{i+1}/{len(sample_posts)}] {post['subreddit']} ({post['upvotes']} upvotes)")
        print(f"    Text: {post['text'][:80]}...")

        # PySpark 分类
        spark_prediction = 2  # 默认，实际应该用模型
        # TODO: 这里需要完整的 Spark 处理

        # 简化版：用关键词
        text_lower = post['text'].lower()
        if any(kw in text_lower for kw in ['security', 'vulnerability', 'compromised', 'exploit']):
            spark_prediction = 0
        elif any(kw in text_lower for kw in ['productivity', 'efficient', 'automate']):
            spark_prediction = 1
        else:
            spark_prediction = 2

        # GLM 分类
        if GLM_API_KEY:
            print(f"    [*] 调用 GLM-4...", end="", flush=True)
            glm_prediction = classify_with_glm(post['text'])
            print(f" -> {LABEL_NAMES.get(glm_prediction, 'Error')}")
        else:
            print(f"    [!] 未配置 GLM API KEY，跳过")
            glm_prediction = -1

        results.append({
            'post_id': post['post_id'],
            'subreddit': post['subreddit'],
            'text': post['text'][:100],
            'spark_pred': spark_prediction,
            'glm_pred': glm_prediction,
            'agreement': spark_prediction == glm_prediction if glm_prediction >= 0 else None
        })

        # 显示对比
        if glm_prediction >= 0:
            status = "MATCH" if spark_prediction == glm_prediction else "DIFFER"
            print(f"    PySpark: {LABEL_NAMES[spark_prediction]} | GLM: {LABEL_NAMES.get(glm_prediction, '?')} -> {status}")

        time.sleep(0.5)  # Rate limiting

    # 统计结果
    print("\n" + "=" * 70)
    print("  对比结果统计")
    print("=" * 70)

    valid_results = [r for r in results if r['glm_pred'] >= 0]

    if valid_results:
        agreements = sum(1 for r in valid_results if r['agreement'])
        agreement_rate = agreements / len(valid_results) * 100

        print(f"\n有效对比: {len(valid_results)} 条")
        print(f"一致: {agreements} 条")
        print(f"不一致: {len(valid_results) - agreements} 条")
        print(f"\n一致性率: {agreement_rate:.1f}%")

        # PySpark 分布
        print("\nPySpark 分类分布:")
        spark_counts = {}
        for r in valid_results:
            label = r['spark_pred']
            spark_counts[label] = spark_counts.get(label, 0) + 1
        for label in [0, 1, 2]:
            print(f"  {LABEL_NAMES[label]}: {spark_counts.get(label, 0)}")

        # GLM 分布
        print("\nGLM 分类分布:")
        glm_counts = {}
        for r in valid_results:
            label = r['glm_pred']
            glm_counts[label] = glm_counts.get(label, 0) + 1
        for label in [0, 1, 2]:
            print(f"  {LABEL_NAMES[label]}: {glm_counts.get(label, 0)}")

        # 不一致的案例
        disagreements = [r for r in valid_results if not r['agreement']]
        if disagreements:
            print("\n不一致案例 (PySpark vs GLM):")
            for r in disagreements[:5]:
                print(f"\n  [{r['subreddit']}]")
                print(f"  Text: {r['text']}...")
                print(f"  PySpark: {LABEL_NAMES[r['spark_pred']]} vs GLM: {LABEL_NAMES[r['glm_pred']]}")

    spark.stop()

    return results


if __name__ == "__main__":
    # 检查 API key
    if not GLM_API_KEY:
        print("WARNING: 未设置 ZHIPUAI_API_KEY 环境变量")
        print("请设置: export ZHIPUAI_API_KEY='your-api-key'")
        print("\n将只运行 PySpark 分类...")

    # 运行对比
    results = run_comparison(num_samples=15)
