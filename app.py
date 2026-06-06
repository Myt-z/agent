"""
花生旅行规划 — Streamlit 前端
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import streamlit as st
from datetime import datetime
from agents.coordinator import TravelCoordinator
from db.database import (
    get_or_create_user, save_plan, get_user_plans,
    get_plan, get_plan_count, get_popular_cities,
)

# ── 页面配置 ──
st.set_page_config(
    page_title="花生 · 你的私人旅行顾问",
    page_icon="🥜",
    layout="wide",
)

# ── 后台管道 ──
from pipeline import start_scheduler

start_scheduler()

# ═══════════════════ CSS ═══════════════════
st.markdown("""
<style>
/* ── 全局变量 ── */
:root {
    --accent: #c97d45;
    --accent-hover: #a8602e;
    --accent-subtle: #fef3e8;
    --accent-light: #fef8f4;
    --bg: #faf8f5;
    --card: #ffffff;
    --text: #1c1917;
    --text-secondary: #78716c;
    --text-tertiary: #a8a29e;
    --border: #e7e5e4;
    --border-light: #f0eeec;
    --radius: 12px;
    --radius-sm: 8px;
}

/* ── 全局覆盖 ── */
.stApp {
    background: #faf8f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e7e5e4;
}
section[data-testid="stSidebar"] .stMarkdown { color: #1c1917; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.3rem; }

/* ── 品牌 ── */
.brand {
    display: flex; align-items: center; gap: 10px;
    font-size: 18px; font-weight: 650; color: #1c1917;
    letter-spacing: -0.3px; margin-bottom: 4px;
}
.brand-icon {
    width: 32px; height: 32px; border-radius: 8px;
    background: #fef3e8; display: flex; align-items: center;
    justify-content: center; font-size: 16px;
}

/* ── 侧边栏区块标题 ── */
.side-label {
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; color: #a8a29e; margin: 14px 0 6px 0;
}

/* ── 统计卡片 ── */
.stat-box {
    display: inline-block; width: 48%;
    background: #faf8f5; border-radius: 8px;
    padding: 10px 12px; text-align: center;
    margin-right: 2%;
}
.stat-num { font-size: 18px; font-weight: 700; color: #1c1917; line-height: 1.2; }
.stat-label { font-size: 10px; color: #a8a29e; }

/* ── 输入框 ── */
.stTextInput > div > div > input {
    border: 1px solid #e7e5e4 !important;
    border-radius: 8px !important;
    background: #faf8f5 !important;
    font-size: 13px !important;
    color: #1c1917 !important;
}
.stTextInput > div > div > input:focus {
    border-color: #c97d45 !important;
    box-shadow: none !important;
}

/* ── 按钮通用 ── */
.stButton > button {
    font-family: inherit !important;
    border-radius: 8px !important;
    transition: all 0.12s !important;
}

/* ── 主按钮（搜索框右侧） ── */
.primary-btn > button {
    background: #c97d45 !important; color: #fff !important;
    border: none !important; font-weight: 550 !important;
    font-size: 14px !important; padding: 10px 24px !important;
}
.primary-btn > button:hover { background: #a8602e !important; }

/* ── 灵感卡片 ── */
.inspo-btn > button {
    background: #ffffff !important; border: 1px solid #e7e5e4 !important;
    border-radius: 12px !important; padding: 16px !important;
    width: 100% !important; text-align: left !important;
    font-size: 13px !important; color: #1c1917 !important;
    min-height: 80px !important;
}
.inspo-btn > button:hover {
    border-color: #c97d45 !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06) !important;
    transform: translateY(-1px);
}
.inspo-emoji { font-size: 28px; display: block; margin-bottom: 6px; }
.inspo-name { font-size: 14px; font-weight: 600; display: block; }
.inspo-tagline { font-size: 11px; color: #a8a29e; }

/* ── 快捷场景按钮 ── */
.preset-btn > button {
    width: 100% !important; text-align: left !important;
    background: #ffffff !important; border: 1px solid #f0eeec !important;
    color: #1c1917 !important; font-size: 13px !important;
    padding: 9px 12px !important; border-radius: 8px !important;
}
.preset-btn > button:hover {
    border-color: #c97d45 !important; color: #c97d45 !important;
    background: #fef8f4 !important;
}

/* ── 最近计划 ── */
.history-btn > button {
    width: 100% !important; text-align: left !important;
    background: transparent !important; border: none !important;
    color: #1c1917 !important; font-size: 13px !important;
    padding: 7px 10px !important; border-radius: 6px !important;
}
.history-btn > button:hover { background: #faf8f5 !important; }
.history-meta { font-size: 11px; color: #a8a29e; }

/* ── 月度推荐 ── */
.pick-btn > button {
    width: 100% !important; text-align: left !important;
    background: transparent !important; border: none !important;
    padding: 8px 10px !important; border-radius: 8px !important;
    color: #1c1917 !important; font-size: 13px !important;
}
.pick-btn > button:hover { background: #faf8f5 !important; }

/* ── 热门标签 ── */
.tag-btn > button {
    background: #faf8f5 !important; border: 1px solid #f0eeec !important;
    border-radius: 100px !important; padding: 4px 10px !important;
    font-size: 11px !important; color: #78716c !important;
    min-height: auto !important; line-height: 1 !important;
}
.tag-btn > button:hover {
    border-color: #c97d45 !important; color: #c97d45 !important;
    background: #fef8f4 !important;
}

/* ── Landing 页 ── */
.landing-tag {
    display: inline-block; padding: 4px 12px; border-radius: 100px;
    font-size: 12px; font-weight: 500; color: #c97d45; background: #fef3e8;
    letter-spacing: 0.3px;
}
.landing h1 { font-size: 38px; font-weight: 700; letter-spacing: -0.9px; line-height: 1.2; margin: 14px 0 8px 0; color: #1c1917; }
.landing h1 em { font-style: normal; color: #c97d45; }
.landing-sub { color: #78716c; font-size: 15px; line-height: 1.7; margin-bottom: 32px; }

/* ── 搜索框区域 ── */
.search-wrap {
    display: flex; align-items: center; gap: 8px;
    background: #ffffff; border: 1px solid #e7e5e4;
    border-radius: 12px; padding: 5px 5px 5px 18px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    max-width: 500px; margin: 0 auto;
}

/* ── 参数行 ── */
.param-row { display: flex; justify-content: center; gap: 28px; margin-top: 16px; }

/* ── 灵感区 ── */
.inspo-label { font-size: 13px; font-weight: 600; letter-spacing: 0.6px; color: #a8a29e; text-transform: uppercase; text-align: center; margin: 48px 0 12px 0; }

/* ── 结果页 ── */
.result-title { font-size: 22px; font-weight: 650; letter-spacing: -0.3px; color: #1c1917; }
.result-body {
    background: #ffffff; border: 1px solid #e7e5e4; border-radius: 12px;
    padding: 36px 40px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    font-size: 14px; line-height: 1.8; color: #1c1917;
}
.result-body h3 { font-size: 16px; font-weight: 650; color: #c97d45 !important; margin: 24px 0 8px 0; }
.result-body h3:first-child { margin-top: 0; }
.result-body strong { font-weight: 600; }

/* ── Footer ── */
.footer { text-align: center; padding: 20px; font-size: 11px; color: #a8a29e; letter-spacing: 0.3px; }

/* ── 隐藏工具栏录制/打印 ── */
[data-testid="stToolbar"] button[title="Record a screencast"],
[data-testid="stToolbar"] button[title="Print"] { display: none !important; }

/* ── 分割线 ── */
.side-hr { border: none; border-top: 1px solid #f0eeec; margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════ 会话初始化 ═══════════════════
defaults = {
    "username": "", "plan_count": 0, "city_count": 0,
    "city": "", "days": 3, "budget": 3000,
    "preferences": "综合体验",
    "result": None, "loading": False, "plan_meta": None,
    "error": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── 月度推荐数据 ──
def get_seasonal_picks():
    month = datetime.now().month
    picks = {
        (3, 4, 5): [
            ("🌸", "武汉", "樱花盛开，东湖春色"),
            ("🏯", "西安", "不冷不热，最适合城墙骑行"),
            ("🌿", "杭州", "烟雨朦胧，龙井新茶"),
        ],
        (6, 7, 8): [
            ("🥬", "桂林", "漓江烟雨正当时"),
            ("🌻", "青海湖", "油菜花季即将到来"),
            ("🏖", "厦门", "不热不燥的海风"),
        ],
        (9, 10, 11): [
            ("🍂", "北京", "香山红叶，秋高气爽"),
            ("🏔", "丽江", "秋色如画，雪山初雪"),
            ("🦀", "苏州", "阳澄湖大闸蟹季"),
        ],
        (12, 1, 2): [
            ("⛷", "哈尔滨", "冰雪大世界正当时"),
            ("♨", "腾冲", "温泉赏银杏"),
            ("🌴", "三亚", "避寒胜地，温暖如春"),
        ],
    }
    for months, p in picks.items():
        if month in months:
            return p
    return picks[(6, 7, 8)]


# ═══════════════════ 侧边栏 ═══════════════════
with st.sidebar:
    # ── 1. 品牌 ──
    st.markdown(
        '<div class="brand"><div class="brand-icon">🥜</div>花生</div>',
        unsafe_allow_html=True,
    )

    # ── 2. 用户 ──
    st.markdown('<div class="side-label">你是谁</div>', unsafe_allow_html=True)
    username = st.text_input(
        "用户名", value=st.session_state.username,
        placeholder="你的名字", label_visibility="collapsed",
        key="username_input",
    )
    if username != st.session_state.username:
        st.session_state.username = username
        st.rerun()

    # ── 3. 旅行记录 ──
    effective_user = st.session_state.username.strip() or "游客"
    user_id = get_or_create_user(effective_user)
    plan_count = get_plan_count(user_id)
    plans_for_cities = get_user_plans(user_id, limit=200)
    city_count = len(set(p["city"] for p in plans_for_cities if p.get("city") != "(智能推荐)"))
    st.session_state.plan_count = plan_count
    st.session_state.city_count = city_count

    st.markdown('<div class="side-label">旅行记录</div>', unsafe_allow_html=True)
    pc = st.session_state.plan_count
    cc = st.session_state.city_count
    st.markdown(
        f'<div class="stat-box"><div class="stat-num">{pc}</div><div class="stat-label">次规划</div></div>'
        f'<div class="stat-box"><div class="stat-num">{cc}</div><div class="stat-label">个城市</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-hr"></div>', unsafe_allow_html=True)

    # ── 4. 一键场景 ──
    st.markdown('<div class="side-label">一键场景</div>', unsafe_allow_html=True)

    presets = [
        ("🏞", "周末两日 · 说走就走", 2, 1500, "综合体验"),
        ("🍲", "美食地图 · 吃遍全城", 3, 2000, "美食探店"),
        ("🏛", "深度人文 · 博物馆之旅", 3, 2500, "历史文化"),
        ("⛰", "户外徒步 · 山水之间", 2, 2000, "自然风光"),
    ]
    for emoji, label, d, b, pref in presets:
        if st.button(
            f"{emoji} {label}", key=f"preset_{label}",
            use_container_width=True,
        ):
            st.session_state.days = d
            st.session_state.budget = b
            st.session_state.preferences = pref
            st.session_state.city = ""
            st.session_state.result = None
            st.session_state.plan_meta = None
            st.session_state.loading = True
            st.session_state._recommend_mode = True
            st.rerun()

    st.markdown('<div class="side-hr"></div>', unsafe_allow_html=True)

    # ── 5. 最近计划 ──
    st.markdown('<div class="side-label">最近计划</div>', unsafe_allow_html=True)
    uid = get_or_create_user(st.session_state.username.strip() or "游客")
    plans = get_user_plans(uid, limit=10)
    if plans:
        for p in plans:
            c = p["city"]
            d = p["days"]
            b = p["budget"]
            label = f"{c} {d}日{' ' * 5}¥{b:,.0f}"
            if st.button(label, key=f"hist_{p['id']}", use_container_width=True):
                full = get_plan(p["id"])
                if full:
                    st.session_state.result = full["result"]
                    st.session_state.plan_meta = {
                        "city": full["city"],
                        "days": full["days"],
                        "budget": full["budget"],
                    }
                    st.rerun()
    else:
        st.caption("还没有计划，去试试吧")

    st.markdown('<div class="side-hr"></div>', unsafe_allow_html=True)

    # ── 6. 当月推荐 ──
    month_names = ["", "一月", "二月", "三月", "四月", "五月", "六月",
                   "七月", "八月", "九月", "十月", "十一月", "十二月"]
    st.markdown(
        f'<div class="side-label">{month_names[datetime.now().month]}推荐</div>',
        unsafe_allow_html=True,
    )
    for emoji, city, reason in get_seasonal_picks():
        if st.button(f"{emoji}  {city}  —  {reason}", key=f"pick_{city}", use_container_width=True):
            st.session_state.city = city
            st.session_state.result = None
            st.session_state.plan_meta = None
            st.session_state.loading = True
            st.session_state._recommend_mode = False
            st.rerun()

    st.markdown('<div class="side-hr"></div>', unsafe_allow_html=True)

    # ── 7. 热门目的地 ──
    st.markdown('<div class="side-label">热门目的地</div>', unsafe_allow_html=True)
    popular = get_popular_cities(8, exclude_username="游客")
    fallback_tags = ["西安", "成都", "重庆", "杭州", "昆明", "长沙", "大理", "拉萨"]
    tag_cities = [p["city"] for p in popular] if popular else fallback_tags

    cols = st.columns(4)
    for i, c in enumerate(tag_cities):
        with cols[i % 4]:
            if st.button(c, key=f"tag_{c}", use_container_width=True):
                st.session_state.city = c
                st.session_state.result = None
                st.session_state.plan_meta = None
                st.session_state.loading = True
                st.session_state._recommend_mode = False
                st.rerun()


# ═══════════════════ 主区域 ═══════════════════

# ── 错误显示 ──
if st.session_state.error:
    st.error(st.session_state.error)
    st.session_state.error = None

# ── Loading 状态 ──
if st.session_state.loading:
    if st.session_state.get("_recommend_mode"):
        with st.spinner("正在智能推荐目的地..."):
            try:
                from agents.recommend_agent import RecommendAgent
                rec = RecommendAgent()
                result = rec.recommend(
                    budget=st.session_state.budget,
                    days=st.session_state.days,
                    preferences=st.session_state.preferences,
                )
                st.session_state.result = result
                try:
                    uid = get_or_create_user(st.session_state.username.strip() or "游客")
                    save_plan(uid, "(智能推荐)", st.session_state.days,
                              st.session_state.budget, st.session_state.preferences, result)
                except Exception:
                    pass
            except Exception as e:
                st.session_state.error = f"推荐失败: {str(e)[:200]}"
                st.session_state.result = None
            finally:
                st.session_state.loading = False
                st.session_state._recommend_mode = False
                st.rerun()
    else:
        with st.spinner("正在为你规划旅程..."):
            try:
                coordinator = TravelCoordinator()
                result = coordinator.plan(
                    city=st.session_state.city.strip(),
                    days=st.session_state.days,
                    budget=st.session_state.budget,
                    preferences=st.session_state.preferences,
                )
                st.session_state.result = result
                try:
                    uid = get_or_create_user(st.session_state.username.strip() or "游客")
                    save_plan(uid, st.session_state.city.strip(),
                              st.session_state.days, st.session_state.budget,
                              st.session_state.preferences, result)
                except Exception:
                    pass
            except Exception as e:
                st.session_state.error = f"规划失败: {str(e)[:200]}"
                st.session_state.result = None
            finally:
                st.session_state.loading = False
                st.rerun()

# ── Result 状态 ──
if st.session_state.result and not st.session_state.loading:
    meta = st.session_state.plan_meta or {}
    display_city = meta.get("city", st.session_state.city)
    display_days = meta.get("days", st.session_state.days)
    display_budget = meta.get("budget", st.session_state.budget)

    # 标题行
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            f'<div class="result-title">{display_city} · {display_days} 日游</div>',
            unsafe_allow_html=True,
        )
    with c2:
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("🔄 重新规划", use_container_width=True, key="replan"):
                st.session_state.result = None
                st.session_state.plan_meta = None
                st.rerun()
        with cc2:
            fname = f"{display_city}_{display_days}日游计划.txt"
            st.download_button(
                "📥 下载", data=st.session_state.result,
                file_name=fname, mime="text/plain",
                use_container_width=True, key="download",
            )

    st.markdown('<div class="result-body">', unsafe_allow_html=True)
    st.markdown(st.session_state.result)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="footer">花生 · 你的私人旅行顾问</div>',
        unsafe_allow_html=True,
    )

# ── Landing 状态 ──
elif not st.session_state.loading:
    # 居中容器
    _, center, _ = st.columns([1, 2, 1])

    with center:
        st.markdown(
            '<div class="landing" style="text-align:center;padding-top:60px">'
            '<span class="landing-tag">AI 旅行规划</span>'
            '<h1>去<em>任何地方</em>，<br>都有人替你规划好一切</h1>'
            '<p class="landing-sub">告诉我们目的地和预算，剩下的交给花生。<br>从行程到预算，从攻略到文化，一站搞定。</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        # 搜索框
        sc1, sc2 = st.columns([4, 1])
        with sc1:
            city_input = st.text_input(
                "目的地", value=st.session_state.city,
                placeholder="想去哪里？输入城市或点击「帮我推荐」",
                label_visibility="collapsed", key="city_input_main",
            )
            if city_input != st.session_state.city:
                st.session_state.city = city_input
        with sc2:
            go = st.button("开始规划", use_container_width=True, key="go_btn",
                           type="primary")

        # 参数行
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            days_val = st.selectbox("天数", list(range(1, 8)),
                                    index=st.session_state.days - 1,
                                    key="days_select")
            if days_val != st.session_state.days:
                st.session_state.days = days_val
        with pc2:
            budget_val = st.number_input("预算 ¥", min_value=500, max_value=100000,
                                         value=st.session_state.budget, step=500,
                                         key="budget_input")
            if budget_val != st.session_state.budget:
                st.session_state.budget = budget_val
        with pc3:
            prefs = ["综合体验", "历史文化", "美食探店", "自然风光", "亲子游"]
            pref_val = st.selectbox("偏好", prefs,
                                    index=prefs.index(st.session_state.preferences)
                                    if st.session_state.preferences in prefs else 0,
                                    key="pref_select")
            if pref_val != st.session_state.preferences:
                st.session_state.preferences = pref_val

        # 触发规划
        from utils.safety import validate_city, sanitize_input, get_submit_guard

        if go:
            city_clean = city_input.strip()
            if not city_clean or city_clean in ("推荐", "不知道", "帮我选"):
                guard = get_submit_guard()
                lock_key = f"{st.session_state.username}-recommend-{st.session_state.days}"
                if guard.try_acquire(lock_key):
                    st.session_state._lock_key = lock_key
                    st.session_state._recommend_mode = True
                    st.session_state.loading = True
                    st.session_state.result = None
                    st.session_state.plan_meta = None
                    st.rerun()
                else:
                    st.warning("正在推荐中，请稍候...")
            else:
                city_clean = sanitize_input(city_clean)
                valid, err = validate_city(city_clean)
                if not valid:
                    st.error(err)
                else:
                    guard = get_submit_guard()
                    lock_key = f"{st.session_state.username}-{city_clean}-{st.session_state.days}"
                    if guard.try_acquire(lock_key):
                        st.session_state._lock_key = lock_key
                        st.session_state.city = city_clean
                        st.session_state._recommend_mode = False
                        st.session_state.loading = True
                        st.session_state.result = None
                        st.session_state.plan_meta = None
                        st.rerun()
                    else:
                        st.warning("相同的规划正在进行中，请稍候...")

        # 灵感卡片
        st.markdown(
            '<div class="inspo-label">热门灵感</div>',
            unsafe_allow_html=True,
        )

        inspos = [
            ("🏯", "西安", "十三朝古都 · 碳水天堂"),
            ("🐼", "成都", "火锅与熊猫的慢生活"),
            ("🏢", "广州", "食在广州 · 早茶文化"),
            ("🌳", "杭州", "西湖畔的烟雨江南"),
        ]
        icols = st.columns(4)
        for i, (emoji, city, tagline) in enumerate(inspos):
            with icols[i]:
                if st.button(
                    f"{emoji}\n\n{city}\n\n{tagline}",
                    key=f"inspo_{city}", use_container_width=True,
                ):
                    st.session_state.city = city
                    st.session_state.result = None
                    st.session_state.plan_meta = None
                    st.session_state.loading = True
                    st.session_state._recommend_mode = False
                    st.rerun()

    st.markdown(
        '<div class="footer">花生 · 你的私人旅行顾问</div>',
        unsafe_allow_html=True,
    )
