"""
独立数据管道 Worker —— 脱离 Streamlit 后台运行。

用法:
  python pipeline_worker.py

打开终端挂着就行，到点自动爬。Ctrl+C 退出。
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from utils.logging import setup_logging, get_logger
setup_logging()
logger = get_logger("pipeline.worker")

from pipeline.scheduler import PipelineScheduler
from pipeline import _pipeline_stats
from rag.knowledge_store import TravelKnowledgeBase


def main():
    print()
    print("=" * 44)
    print("  数据管道 Worker")
    print("=" * 44)
    print()

    # ── 知识库 ──
    logger.info("加载知识库...")
    kb = TravelKnowledgeBase()
    kb.load()
    report = kb.freshness_report()
    print(f"  知识库: {report['total_docs']} 条文档")
    print(f"    web: {report['web_docs']} | local: {report['local_docs']}")
    print(f"    新鲜: {report['fresh_7d']} | 陈旧: {report['stale_30d']} | 过期: {report['expired']}")
    print()

    # ── 调度器 ──
    scheduler = PipelineScheduler()
    scheduler.start()
    print(f"  调度器已启动")
    print(f"    Hot  每 {scheduler.hot_interval}h | Warm  每 {scheduler.warm_interval}h")
    print(f"    Cleanup  每 24h")
    print()
    print("  Ctrl+C 退出")
    print()

    # ── 主循环 ──
    try:
        while True:
            time.sleep(60)
            stats = _pipeline_stats
            if stats["runs"] > 0:
                last = stats.get("last_run", "N/A")
                if last:
                    last = last[:19]
                print(f"  [{time.strftime('%H:%M:%S')}] runs={stats['runs']}  "
                      f"errors={stats['errors']}  last={last}")
    except KeyboardInterrupt:
        print()
        logger.info("Worker 退出")
        scheduler.scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
