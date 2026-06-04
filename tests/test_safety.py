"""
测试安全层：输入校验、降级处理器、防重复提交、重试
"""
import time
import pytest


class TestValidateCity:
    """输入校验：城市名边界条件"""

    def test_valid_city(self):
        from utils.safety import validate_city
        ok, err = validate_city("西安")
        assert ok
        assert err == ""

    def test_empty_city(self):
        from utils.safety import validate_city
        ok, err = validate_city("")
        assert not ok
        assert "不能为空" in err

    def test_whitespace_only(self):
        from utils.safety import validate_city
        ok, err = validate_city("   ")
        assert not ok

    def test_too_long_city(self):
        from utils.safety import validate_city
        long_name = "A" * 100
        ok, err = validate_city(long_name)
        assert not ok
        assert "不能超过" in err

    def test_xss_injection(self):
        from utils.safety import validate_city
        ok, err = validate_city("<script>alert('xss')</script>")
        assert not ok

    def test_sql_injection(self):
        from utils.safety import validate_city
        ok, err = validate_city("'; DROP TABLE users; --")
        assert not ok


class TestValidatePreferences:
    """偏好校验"""

    def test_valid_preference(self):
        from utils.safety import validate_preferences
        assert validate_preferences("历史文化") == "历史文化"

    def test_invalid_returns_default(self):
        from utils.safety import validate_preferences
        assert validate_preferences("乱七八糟") == "综合体验"


class TestSanitize:
    """输入清理"""

    def test_strip_whitespace(self):
        from utils.safety import sanitize_input
        assert sanitize_input("  西安  ") == "西安"

    def test_remove_control_chars(self):
        from utils.safety import sanitize_input
        assert "\x00" not in sanitize_input("西\x00安")


class TestDegradationHandler:
    """降级处理器：服务挂了用户不看到 500"""

    def test_primary_succeeds(self):
        from utils.safety import DegradationHandler
        h = DegradationHandler()
        result = h.try_or_degrade(
            primary=lambda: "成功",
            fallback="兜底",
        )
        assert result == "成功"
        assert h.report()["total"] == 0

    def test_fallback_on_failure(self):
        from utils.safety import DegradationHandler
        h = DegradationHandler()
        result = h.try_or_degrade(
            primary=lambda: 1 / 0,  # 故意抛异常
            fallback="服务暂不可用",
        )
        assert result == "服务暂不可用"
        assert h.report()["total"] == 1

    def test_fallback_callable(self):
        from utils.safety import DegradationHandler
        h = DegradationHandler()
        result = h.try_or_degrade(
            primary=lambda: 1 / 0,
            fallback=lambda: "动态兜底",
        )
        assert result == "动态兜底"


class TestSubmitGuard:
    """防重复提交"""

    def test_first_acquire_succeeds(self):
        from utils.safety import SubmitGuard
        g = SubmitGuard()
        assert g.try_acquire("key1")

    def test_second_acquire_fails(self):
        from utils.safety import SubmitGuard
        g = SubmitGuard()
        g.try_acquire("key2")
        assert not g.try_acquire("key2")

    def test_release_allows_reacquire(self):
        from utils.safety import SubmitGuard
        g = SubmitGuard()
        g.try_acquire("key3")
        g.release("key3")
        assert g.try_acquire("key3")

    def test_timeout_auto_release(self):
        from utils.safety import SubmitGuard
        g = SubmitGuard()
        g.try_acquire("key4", timeout=0.05)  # 0.05 秒过期
        time.sleep(0.3)  # 等待锁过期
        assert g.try_acquire("key4", timeout=0.05)  # 传相同 timeout 触发清理


class TestRetry:
    """重试装饰器"""

    def test_retry_succeeds_eventually(self):
        from utils.safety import retry_on_failure
        call_count = [0]

        @retry_on_failure(max_attempts=3, delay=0.01)
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("临时故障")
            return "成功"

        result = flaky_func()
        assert result == "成功"
        assert call_count[0] == 3

    def test_retry_exhausted(self):
        from utils.safety import retry_on_failure

        @retry_on_failure(max_attempts=2, delay=0.01)
        def always_fail():
            raise RuntimeError("永远失败")

        with pytest.raises(RuntimeError):
            always_fail()
