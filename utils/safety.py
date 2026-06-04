"""
安全层 —— 输入的边界在哪，出错时怎么降级

三个职责：
  1. 输入校验：不为空、不超长、不含危险字符
  2. 错误降级：上游服务挂了，用户看到的不是 500 而是友好提示
  3. 防重复：用户连点两次"开始规划"不会发起两次 Agent 调用
"""
import re
import time
import functools
import logging

logger = logging.getLogger("travel-planner.safety")

# ============================================================
# 输入校验
# ============================================================

MAX_CITY_LENGTH = 50
MAX_PREFERENCES_LENGTH = 20
FORBIDDEN_PATTERNS = [
    r"<script",     # XSS
    r"DROP\s+TABLE",  # SQL injection（虽然我们用参数化查询，但防御深度）
    r"'.*--",       # SQL 注释注入
]


def validate_city(city: str) -> tuple[bool, str]:
    """
    校验城市名输入。
    返回: (是否合法, 错误信息)
    """
    if not city or not city.strip():
        return False, "城市名不能为空"

    city = city.strip()

    if len(city) > MAX_CITY_LENGTH:
        return False, f"城市名不能超过 {MAX_CITY_LENGTH} 个字符"

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, city, re.IGNORECASE):
            logger.warning(f"检测到可疑输入: {city[:30]}...")
            return False, "输入包含无效字符，请重新输入"

    return True, ""


def validate_preferences(prefs: str) -> str:
    """校验偏好，非法值返回默认"""
    valid = ["综合体验", "历史文化", "美食探店", "自然风光", "购物血拼", "亲子游"]
    if prefs in valid:
        return prefs
    return "综合体验"


def sanitize_input(text: str) -> str:
    """清理用户输入：去首尾空格、去控制字符、截断"""
    text = text.strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)  # 去控制字符
    return text


# ============================================================
# 错误降级
# ============================================================

class DegradationHandler:
    """
    降级处理器 —— 某个服务挂了，不影响用户看到有用信息。

    用法：
      handler = DegradationHandler()
      result = handler.try_or_degrade(
          primary=lambda: call_duckduckgo(query),
          fallback="搜索服务暂时不可用，基于本地知识库回答",
      )
    """

    def __init__(self):
        self.degradations = []  # 记录所有降级事件（用于监控）

    def try_or_degrade(self, primary, fallback, context: str = ""):
        """
        尝试执行 primary，失败则返回 fallback。
        不抛异常，不中断用户流程。
        """
        try:
            return primary()
        except Exception as e:
            msg = f"[降级] {context}: {type(e).__name__}: {str(e)[:100]}"
            logger.warning(msg)
            self.degradations.append(msg)
            return fallback() if callable(fallback) else fallback

    def report(self) -> dict:
        """获取降级报告"""
        return {
            "total": len(self.degradations),
            "events": self.degradations[-5:],  # 最近 5 条
        }


# 全局单例
_degradation_handler = DegradationHandler()


def get_degradation_handler():
    return _degradation_handler


# ============================================================
# 防重复提交
# ============================================================

class SubmitGuard:
    """
    防重复提交 —— 用户连点两次按钮，只处理第一次。

    用法：
      guard = SubmitGuard()
      if guard.try_acquire("user-plan"):
          plan()
          guard.release("user-plan")
    """

    def __init__(self):
        self._locks: dict[str, tuple[float, float]] = {}  # key → (timestamp, timeout)

    def try_acquire(self, key: str, timeout: float = 120) -> bool:
        """
        尝试获取锁。
        key: 锁标识（如 user_id + city）
        timeout: 锁超时时间（秒），防止死锁

        返回: True=可以执行, False=已有相同任务在执行
        """
        now = time.time()
        # 清理过期锁（用每个锁自己的 timeout）
        for k in list(self._locks.keys()):
            ts, to = self._locks[k]
            if now - ts > to:
                del self._locks[k]

        if key in self._locks:
            return False

        self._locks[key] = (now, timeout)
        return True

    def release(self, key: str):
        """释放锁"""
        self._locks.pop(key, None)


_submit_guard = SubmitGuard()


def get_submit_guard():
    return _submit_guard


# ============================================================
# 重试装饰器
# ============================================================

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """
    装饰器：失败自动重试。

    适用于：网络请求、API 调用等不稳定的操作。
    不适用于：逻辑错误（重试也不会好）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"[重试] {func.__name__} 第{attempt+1}次失败: {e}，"
                            f"{delay}秒后重试..."
                        )
                        time.sleep(delay)
            raise last_error
        return wrapper
    return decorator
