"""
LLM 调用追踪器 —— 调试大模型的必备工具

用途：记录每次 LLM 调用的输入/输出/耗时/token，帮你排查问题。

使用方法：
  from debug.tracer import trace_llm

  @trace_llm
  def my_function():
      ...

  # 或者用上下文管理器：
  with LLMTracer() as tracer:
      agent.invoke(...)
      tracer.print_summary()
"""

import time
import functools
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMCall:
    """一次 LLM 调用的完整记录"""
    call_id: int
    model: str = ""
    input_messages: list = field(default_factory=list)
    output_content: str = ""
    tool_calls: list = field(default_factory=list)
    duration_seconds: float = 0
    token_usage: dict = field(default_factory=dict)
    error: str = ""


class LLMTracer:
    """
    LLM 调用追踪器。

    收集每次调用的信息，结束后可打印汇总报告。
    """

    def __init__(self):
        self.calls: list[LLMCall] = []
        self._call_count = 0

    def record(
        self,
        model: str = "",
        input_messages: list | None = None,
        output_content: str = "",
        tool_calls: list | None = None,
        duration: float = 0,
        token_usage: dict | None = None,
        error: str = "",
    ):
        """手动记录一次 LLM 调用"""
        self._call_count += 1
        self.calls.append(LLMCall(
            call_id=self._call_count,
            model=model,
            input_messages=input_messages or [],
            output_content=output_content,
            tool_calls=tool_calls or [],
            duration_seconds=duration,
            token_usage=token_usage or {},
            error=error,
        ))

    def print_summary(self):
        """打印汇总报告"""
        if not self.calls:
            print("[Tracer] 没有记录到 LLM 调用")
            return

        print("\n" + "=" * 60)
        print(f"  LLM 调用追踪报告（共 {len(self.calls)} 次调用）")
        print("=" * 60)

        total_tokens = 0
        total_duration = 0

        for call in self.calls:
            status = "FAIL" if call.error else "OK"
            tokens = call.token_usage.get("total_tokens", "?")
            if isinstance(tokens, int):
                total_tokens += tokens

            print(f"\n  调用 #{call.call_id} [{status}] {call.duration_seconds:.1f}s")
            print(f"  模型: {call.model}")

            # 输入摘要
            if call.input_messages:
                last_msg = call.input_messages[-1]
                content_preview = str(last_msg.get("content", ""))[:80]
                print(f"  输入: {content_preview}...")

            # 工具调用
            if call.tool_calls:
                for tc in call.tool_calls:
                    name = tc.get("name", "unknown")
                    args = str(tc.get("args", {}))[:60]
                    print(f"  调用工具: {name}({args})")

            # 输出摘要
            if call.output_content:
                preview = call.output_content[:100].replace("\n", " ")
                print(f"  输出: {preview}...")

            # 错误
            if call.error:
                print(f"  错误: {call.error}")

            print(f"  Token: {tokens}")
            total_duration += call.duration

        print(f"\n  {'─' * 50}")
        print(f"  总耗时: {total_duration:.1f}s | 总 Token: {total_tokens}")
        print("=" * 60)


# 全局单例
_global_tracer: LLMTracer | None = None


def get_tracer() -> LLMTracer:
    """获取全局追踪器实例"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = LLMTracer()
    return _global_tracer


def reset_tracer():
    """重置全局追踪器"""
    global _global_tracer
    _global_tracer = LLMTracer()


def trace_llm(func):
    """
    装饰器：自动追踪 LLM 调用。

    要求被装饰的函数返回 (output_content, tool_calls, token_usage) 元组。
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracer = get_tracer()
        start = time.time()
        try:
            output_content, tool_calls, token_usage = func(*args, **kwargs)
            duration = time.time() - start
            tracer.record(
                model=getattr(func, "__name__", "unknown"),
                input_messages=kwargs.get("messages", []),
                output_content=output_content,
                tool_calls=tool_calls or [],
                duration=duration,
                token_usage=token_usage or {},
            )
            return output_content, tool_calls, token_usage
        except Exception as e:
            duration = time.time() - start
            tracer.record(
                model=getattr(func, "__name__", "unknown"),
                error=str(e),
                duration=duration,
            )
            raise

    return wrapper
