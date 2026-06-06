"""
数据管道 —— 定时爬取 + 增量更新 + 过期清理

主动维护 ChromaDB 知识库的新鲜度，不再等用户查询时才被动刷新。
"""
import os
import threading
from datetime import datetime

_pipeline_stats = {
    "last_run": None,
    "runs": 0,
    "errors": 0,
    "last_hot_run": None,
    "last_warm_run": None,
    "last_cleanup_run": None,
}

_pipeline_lock = threading.Lock()

_scheduler_started = False


def get_pipeline_stats() -> dict:
    with _pipeline_lock:
        return dict(_pipeline_stats)


def start_scheduler():
    global _scheduler_started
    if _scheduler_started:
        return

    enabled = os.getenv("PIPELINE_ENABLED", "true").lower() == "true"
    if not enabled:
        return

    try:
        from pipeline.scheduler import PipelineScheduler

        scheduler = PipelineScheduler()
        scheduler.start()
        _scheduler_started = True
    except ImportError:
        from utils.logging import get_logger
        get_logger("pipeline").warning("apscheduler 未安装，后台数据管道不可用")
    except Exception as e:
        from utils.logging import get_logger
        get_logger("pipeline").error(f"调度器启动失败: {e}", exc_info=True)
