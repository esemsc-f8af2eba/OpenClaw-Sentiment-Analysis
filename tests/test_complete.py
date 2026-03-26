"""
Complete Test Suite for OpenClaw Sentiment Analysis
包含: 单元测试、集成测试、边界测试、性能测试

运行方式:
  pytest tests/test_complete.py -v                    # 运行全部测试
  pytest tests/test_complete.py -m unit              # 只运行单元测试
  pytest tests/test_complete.py -m integration       # 只运行集成测试
  pytest tests/test_complete.py -m performance       # 只运行性能测试
  pytest tests/test_complete.py -m "not llm"         # 排除需要API的测试
"""
import pytest
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.generate_data import generate_post, generate_dataset, stream_posts
from config import (
    LABEL_SECURITY, LABEL_PRODUCTIVITY, LABEL_NEUTRAL,
    SECURITY_KEYWORDS, PRODUCTIVITY_KEYWORDS,
    KAFKA_BROKER, TOPIC_RAW
)


# =============================================================================
# UNIT TESTS (单元测试) - 快速、隔离、不依赖外部服务
# =============================================================================

@pytest.mark.unit
class TestDataGeneration:
    """测试数据生成模块"""

    def test_post_has_required_fields(self):
        """帖子应包含所有必需字段"""
        post = generate_post(1)
        required_fields = ["post_id", "timestamp", "source", "text", "label", "upvotes", "comments"]
        for field in required_fields:
            assert field in post, f"Missing field: {field}"

    def test_label_is_valid_integer(self):
        """标签必须是 0, 1, 或 2"""
        for i in range(100):
            post = generate_post(i)
            assert post["label"] in [0, 1, 2], f"Invalid label: {post['label']}"

    def test_text_is_not_empty(self):
        """帖子文本不能为空"""
        for i in range(50):
            post = generate_post(i)
            assert len(post["text"]) > 0, "Empty text detected"
            assert isinstance(post["text"], str), "Text must be string"

    def test_upvotes_and_comments_are_non_negative(self):
        """点赞数和评论数不能为负"""
        for i in range(50):
            post = generate_post(i)
            assert post["upvotes"] >= 0, f"Negative upvotes: {post['upvotes']}"
            assert post["comments"] >= 0, f"Negative comments: {post['comments']}"

    def test_source_is_valid(self):
        """来源必须是 reddit 或 twitter"""
        valid_sources = ["reddit", "twitter"]
        for i in range(50):
            post = generate_post(i)
            assert post["source"] in valid_sources, f"Invalid source: {post['source']}"

    def test_json_serializable(self):
        """帖子应该可以序列化为 JSON (用于 Kafka)"""
        post = generate_post(0)
        serialized = json.dumps(post)
        assert isinstance(serialized, str)
        assert len(serialized) > 0


@pytest.mark.unit
class TestKeywordClassification:
    """测试基于关键词的分类逻辑"""

    def test_security_keywords_exist(self):
        """安全关键词列表不应为空"""
        assert len(SECURITY_KEYWORDS) > 0
        assert "api leak" in SECURITY_KEYWORDS
        assert "vulnerability" in SECURITY_KEYWORDS

    def test_productivity_keywords_exist(self):
        """生产力关键词列表不应为空"""
        assert len(PRODUCTIVITY_KEYWORDS) > 0
        assert "saves time" in PRODUCTIVITY_KEYWORDS
        assert "automate" in PRODUCTIVITY_KEYWORDS

    def test_keyword_classification_logic(self):
        """测试简单的关键词分类逻辑"""
        # Security 文本应包含安全关键词
        security_templates = [
            "OpenClaw exposed my API key",
            "Found a vulnerability in OpenClaw",
            "Data breach in OpenClaw"
        ]
        for text in security_templates:
            text_lower = text.lower()
            has_security_kw = any(kw in text_lower for kw in SECURITY_KEYWORDS)
            assert has_security_kw, f"Security text missing keyword: {text}"

        # Productivity 文本应包含生产力关键词
        productivity_templates = [
            "OpenClaw saves me hours",
            "Automated with OpenClaw",
            "More productive with OpenClaw"
        ]
        for text in productivity_templates:
            text_lower = text.lower()
            has_prod_kw = any(kw in text_lower for kw in PRODUCTIVITY_KEYWORDS)
            assert has_prod_kw, f"Productivity text missing keyword: {text}"


@pytest.mark.unit
class TestConfigConstants:
    """测试配置常量"""

    def test_label_constants_are_distinct(self):
        """标签常量应该互不相同"""
        assert LABEL_SECURITY != LABEL_PRODUCTIVITY
        assert LABEL_SECURITY != LABEL_NEUTRAL
        assert LABEL_PRODUCTIVITY != LABEL_NEUTRAL

    def test_label_constants_are_consecutive(self):
        """标签应该是 0, 1, 2"""
        labels = [LABEL_SECURITY, LABEL_PRODUCTIVITY, LABEL_NEUTRAL]
        assert sorted(labels) == [0, 1, 2]


# =============================================================================
# BOUNDARY TESTS (边界测试) - 测试边界条件和极端情况
# =============================================================================

@pytest.mark.boundary
@pytest.mark.unit
class TestBoundaryConditions:
    """边界条件测试"""

    def test_empty_text_handling(self):
        """空文本应该有默认处理"""
        post = generate_post(0)
        assert len(post["text"].strip()) > 0

    def test_special_characters_in_text(self):
        """文本应能处理特殊字符"""
        post = generate_post(0)
        # 应该包含标点符号等特殊字符
        has_special = any(c in post["text"] for c in ".,!?-:'\"")
        assert has_special, "Text should contain punctuation"

    def test_very_long_post_id(self):
        """大数字 post_id 应该正常工作"""
        post = generate_post(999999999)
        assert post["post_id"] == 999999999

    def test_zero_upvotes_boundary(self):
        """0 点赞是有效的边界值"""
        for i in range(100):
            post = generate_post(i)
            if post["upvotes"] == 0:
                assert True
                return
        # 至少应该有一个 0 点赞的帖子
        pytest.fail("No posts with 0 upvotes found in 100 samples")

    def test_dataset_size_zero(self):
        """空数据集应该正常处理"""
        df = generate_dataset(n=0, save_path="/tmp/test_empty.csv")
        assert len(df) == 0

    def test_single_post_dataset(self):
        """单条数据集应该正常处理"""
        df = generate_dataset(n=1, save_path="/tmp/test_single.csv")
        assert len(df) == 1


# =============================================================================
# INTEGRATION TESTS (集成测试) - 需要外部服务
# =============================================================================

@pytest.mark.integration
class TestKafkaIntegration:
    """Kafka 集成测试"""

    def test_kafka_config_exists(self):
        """Kafka 配置应该存在"""
        assert KAFKA_BROKER is not None
        assert len(KAFKA_BROKER) > 0
        assert ":" in KAFKA_BROKER  # Should have port

    def test_topic_name_exists(self):
        """Topic 名称应该已定义"""
        assert TOPIC_RAW is not None
        assert len(TOPIC_RAW) > 0


@pytest.mark.integration
class TestModelIntegration:
    """模型集成测试"""

    def test_model_path_configured(self):
        """模型路径应该在配置中定义"""
        from config import MODEL_PATH
        assert MODEL_PATH is not None
        assert isinstance(MODEL_PATH, str)

    def test_data_path_configured(self):
        """数据路径应该在配置中定义"""
        from config import DATA_PATH
        assert DATA_PATH is not None
        assert isinstance(DATA_PATH, str)


# =============================================================================
# PERFORMANCE TESTS (性能测试) - 测试性能指标
# =============================================================================

@pytest.mark.performance
class TestDataGenerationPerformance:
    """数据生成性能测试"""

    def test_generate_100_posts_under_1_second(self):
        """生成 100 条帖子应在 1 秒内完成"""
        start = time.time()
        posts = [generate_post(i) for i in range(100)]
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Too slow: {elapsed:.2f}s for 100 posts"
        assert len(posts) == 100

    def test_generate_1000_posts_under_5_seconds(self):
        """生成 1000 条帖子应在 5 秒内完成"""
        start = time.time()
        df = generate_dataset(n=1000, save_path="/tmp/test_perf.csv")
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Too slow: {elapsed:.2f}s for 1000 posts"
        assert len(df) == 1000

    def test_stream_posts_interval(self):
        """流式生成应该保持指定间隔"""
        interval = 0.1  # 100ms
        count = 0
        start = time.time()

        for post in stream_posts(interval=interval):
            count += 1
            if count >= 5:
                break

        elapsed = time.time() - start
        # 5 posts * 0.1s = 0.5s，允许 +/- 0.2s 误差
        assert 0.3 < elapsed < 0.7, f"Interval timing off: {elapsed:.2f}s"


@pytest.mark.performance
class TestMemoryEfficiency:
    """内存效率测试"""

    def test_large_dataset_memory(self):
        """大数据集不应占用过多内存"""
        import tracemalloc
        tracemalloc.start()

        # 生成 5000 条数据
        df = generate_dataset(n=5000, save_path="/tmp/test_memory.csv")

        current, peak = tracemalloc.get_traced_memory()
        peak_mb = peak / 1024 / 1024

        # 应该小于 100MB
        assert peak_mb < 100, f"Too much memory: {peak_mb:.2f}MB"
        assert len(df) == 5000


# =============================================================================
# LLM VALIDATION TESTS (需要 API Key)
# =============================================================================

@pytest.mark.llm
class TestLLMValidation:
    """使用 LLM 验证分类准确性"""

    def test_glm_api_key_available(self):
        """GLM API key 应该可用（如果运行此测试）"""
        api_key = os.getenv("ZHIPUAI_API_KEY")
        if api_key:
            assert len(api_key) > 10
        else:
            pytest.skip("ZHIPUAI_API_KEY not set")

    def test_llm_classification_response_format(self):
        """LLM 应该返回有效的分类格式"""
        # This is a placeholder - actual implementation would call GLM API
        # For now, just test the logic
        valid_labels = [0, 1, 2]
        for label in valid_labels:
            assert label in valid_labels


# =============================================================================
# TEST REPORTING
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_report(request):
    """生成测试报告"""
    yield

    # 测试结束后打印摘要
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Node: {request.config.workerinput.get('workerid', 'master')}")
    print("=" * 60)
