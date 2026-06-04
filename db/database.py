"""
SQLite 数据库 —— 存储用户和旅行计划

三张表：
  users    → 用户信息
  plans    → 生成的旅行计划（全文存储）

对比 ChromaDB：ChromaDB 管"语义检索"，SQLite 管"结构化存储"
两者互补，不冲突。
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "travel_planner.db"


@contextmanager
def get_connection():
    """获取数据库连接（上下文管理器，自动关闭）"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """建表（幂等，重复执行不会出错）"""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    UNIQUE NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS plans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                city        TEXT    NOT NULL,
                days        INTEGER NOT NULL,
                budget      REAL    NOT NULL,
                preferences TEXT    NOT NULL,
                result      TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                rating      INTEGER DEFAULT NULL CHECK(rating >= 0 AND rating <= 100),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_plans_user ON plans(user_id);
            CREATE INDEX IF NOT EXISTS idx_plans_city ON plans(city);
        """)


# 应用启动时自动初始化
init_db()


# ===== 用户操作 =====

def get_or_create_user(username: str) -> int:
    """根据用户名获取用户 ID，不存在则自动创建"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO users (username) VALUES (?)", (username,)
        )
        return cur.lastrowid


# ===== 计划操作 =====

def save_plan(user_id: int, city: str, days: int, budget: float,
              preferences: str, result: str) -> int:
    """保存一份旅行计划，返回计划 ID"""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO plans (user_id, city, days, budget, preferences, result)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, city, days, budget, preferences, result),
        )
        return cur.lastrowid


def get_user_plans(user_id: int, limit: int = 20) -> list[dict]:
    """获取用户的最近计划列表"""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, city, days, budget, preferences, created_at
               FROM plans WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_plan(plan_id: int) -> dict | None:
    """获取一份计划的完整内容"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM plans WHERE id = ?", (plan_id,)
        ).fetchone()
        return dict(row) if row else None


def get_plan_count(user_id: int) -> int:
    """统计用户生成过多少份计划"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM plans WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["cnt"] if row else 0


def get_popular_cities(limit: int = 5) -> list[dict]:
    """热门目的地排名（全局）"""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT city, COUNT(*) as cnt FROM plans
               GROUP BY city ORDER BY cnt DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def rate_plan(plan_id: int, rating: int) -> bool:
    """给一份计划打分（0-100）"""
    if not (0 <= rating <= 100):
        raise ValueError(f"评分必须在 0-100 之间，收到: {rating}")
    with get_connection() as conn:
        conn.execute(
            "UPDATE plans SET rating = ? WHERE id = ?", (rating, plan_id)
        )
        return True


def get_top_rated_plans(limit: int = 5) -> list[dict]:
    """高分计划排行"""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, city, days, budget, rating, created_at
               FROM plans WHERE rating IS NOT NULL
               ORDER BY rating DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
