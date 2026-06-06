"""
调度器 —— APScheduler 定时触发爬取任务。

三层节奏：
  Hot  (4h)  → 热门城市，从 SQLite 取 Top-N
  Warm (24h) → 本地攻略城市，排除 Hot 已覆盖的
  Cold (24h) → 清理超过 30 天的 web 文档
"""
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from utils.logging import get_logger

logger = get_logger("pipeline.scheduler")


class PipelineScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)

        self.hot_interval = int(os.getenv("PIPELINE_HOT_INTERVAL", "4"))
        self.warm_interval = int(os.getenv("PIPELINE_WARM_INTERVAL", "24"))
        self.hot_count = int(os.getenv("PIPELINE_HOT_COUNT", "5"))
        self.queries_per_city = int(os.getenv("PIPELINE_QUERIES_PER_CITY", "4"))
        self.web_cache_days = int(os.getenv("WEB_CACHE_DAYS", "30"))

        self._kb = None

    @property
    def kb(self):
        if self._kb is None:
            from rag.knowledge_store import TravelKnowledgeBase

            self._kb = TravelKnowledgeBase()
            self._kb.load()
        return self._kb

    def start(self):
        self.scheduler.add_job(
            self._run_hot,
            trigger="interval",
            hours=self.hot_interval,
            id="pipeline_hot",
            name="Hot 层刷新",
            next_run_time=datetime.now(),  # 启动后立即跑一次
        )
        self.scheduler.add_job(
            self._run_warm,
            trigger="interval",
            hours=self.warm_interval,
            id="pipeline_warm",
            name="Warm 层刷新",
            next_run_time=datetime.now(),
        )
        self.scheduler.add_job(
            self._run_cleanup,
            trigger="interval",
            hours=24,
            id="pipeline_cleanup",
            name="过期清理",
            next_run_time=datetime.now(),
        )

        self.scheduler.start()
        logger.info(
            f"调度器已启动 | hot={self.hot_interval}h | warm={self.warm_interval}h"
        )

    def _run_hot(self):
        from pipeline.crawler import crawl_city, get_hot_cities
        from pipeline import _pipeline_stats, _pipeline_lock

        logger.info("Hot 层刷新开始")
        try:
            cities = get_hot_cities(self.hot_count)
            if not cities:
                from pipeline.crawler import get_all_cities
                cities = get_all_cities()[: self.hot_count]

            logger.info(f"Hot 城市: {cities}")
            for city in cities:
                try:
                    crawl_city(self.kb, city, num_queries=self.queries_per_city)
                except Exception as e:
                    logger.error(f"Hot 爬取失败 [{city}]: {e}")
                    with _pipeline_lock:
                        _pipeline_stats["errors"] += 1

            with _pipeline_lock:
                _pipeline_stats["runs"] += 1
                _pipeline_stats["last_hot_run"] = datetime.now().isoformat()
                _pipeline_stats["last_run"] = _pipeline_stats["last_hot_run"]
        except Exception as e:
            logger.error(f"Hot 层调度异常: {e}")
            with _pipeline_lock:
                _pipeline_stats["errors"] += 1

    def _run_warm(self):
        from pipeline.crawler import crawl_city, get_hot_cities, get_warm_cities
        from pipeline import _pipeline_stats, _pipeline_lock

        logger.info("Warm 层刷新开始")
        try:
            hot = get_hot_cities(self.hot_count)
            cities = get_warm_cities(hot)

            logger.info(f"Warm 城市: {cities}")
            for city in cities:
                try:
                    crawl_city(self.kb, city, num_queries=self.queries_per_city)
                except Exception as e:
                    logger.error(f"Warm 爬取失败 [{city}]: {e}")
                    with _pipeline_lock:
                        _pipeline_stats["errors"] += 1

            with _pipeline_lock:
                _pipeline_stats["last_warm_run"] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Warm 层调度异常: {e}")
            with _pipeline_lock:
                _pipeline_stats["errors"] += 1

    def _run_cleanup(self):
        from pipeline.crawler import cleanup_expired
        from pipeline import _pipeline_stats, _pipeline_lock

        logger.info("过期清理开始")
        try:
            deleted = cleanup_expired(self.kb, self.web_cache_days)
            with _pipeline_lock:
                _pipeline_stats["last_cleanup_run"] = datetime.now().isoformat()
            logger.info(f"过期清理完成: {deleted} 条")
        except Exception as e:
            logger.error(f"清理异常: {e}")
            with _pipeline_lock:
                _pipeline_stats["errors"] += 1
