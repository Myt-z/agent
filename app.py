"""
知行旅行规划助手 — 浏览器界面

运行方式：
  streamlit run app.py

浏览器自动打开 http://localhost:8501
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import streamlit as st
from agents.coordinator import TravelCoordinator
from db.database import get_or_create_user, save_plan, get_user_plans, get_plan, get_plan_count, get_popular_cities


# ── 页面配置 ──
st.set_page_config(
    page_title="知行旅行规划助手",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 知行旅行规划助手")
st.caption("基于 LangChain 多 Agent 协作的 AI 旅行规划器")

# ── 侧边栏：输入参数 ──
with st.sidebar:
    # 用户名
    st.header("用户")
    if "username" not in st.session_state:
        st.session_state.username = ""
    username = st.text_input("你的名字", value=st.session_state.username, placeholder="输入名字以保存计划")
    if username != st.session_state.username:
        st.session_state.username = username
        st.rerun()

    st.divider()
    st.header("旅行需求")

    city = st.text_input(
        "目的地（留空或输入"推荐"可智能推荐）",
        placeholder="西安 / 广州 / 成都... 或留空让我推荐",
    )

    days = st.slider("游玩天数", min_value=1, max_value=14, value=3)

    budget = st.number_input(
        "总预算（元）",
        min_value=500,
        max_value=100000,
        value=3000,
        step=500,
    )

    preferences = st.selectbox(
        "旅行偏好",
        ["综合体验", "历史文化", "美食探店", "自然风光", "购物血拼", "亲子游"],
    )

    go_button = st.button("🚀 开始规划", type="primary", use_container_width=True)

    st.divider()

    # 历史记录
    if st.session_state.username.strip():
        user_id = get_or_create_user(st.session_state.username.strip())
        plans = get_user_plans(user_id, limit=10)

        if plans:
            st.caption(f"你的历史计划（{get_plan_count(user_id)} 份）")
            for p in plans:
                label = f"{p['city']} {p['days']}天 ¥{p['budget']:.0f}"
                if st.button(label, key=f"plan_{p['id']}", use_container_width=True):
                    full = get_plan(p["id"])
                    if full:
                        st.session_state.result = full["result"]
                        st.rerun()

    st.divider()

    # 热门目的地
    popular = get_popular_cities(5)
    if popular:
        st.caption("热门目的地")
        for p in popular:
            st.caption(f"{p['city']}（{p['cnt']} 次）")

    st.divider()
    from llm.factory import get_model_info
    info = get_model_info()
    st.caption(f"环境: {info['env']} | 模型: {info.get('provider','mock')}/{info.get('model','')}")
    st.caption("技术栈：LangChain + ChromaDB + SQLite + DeepSeek")


# ── 主区域 ──
if "result" not in st.session_state:
    st.session_state.result = None
if "loading" not in st.session_state:
    st.session_state.loading = False

if go_button:
    from utils.safety import validate_city, get_submit_guard, sanitize_input

    # 未输入城市 → 智能推荐模式
    if not city.strip() or city.strip() in ("推荐", "不知道", "帮我选"):
        guard = get_submit_guard()
        lock_key = f"{st.session_state.username}-recommend-{days}"
        if not guard.try_acquire(lock_key):
            st.warning("正在推荐中，请稍候...")
        else:
            st.session_state._lock_key = lock_key
            st.session_state._recommend_mode = True
            st.session_state.loading = True
            st.session_state.result = None
    else:
        city = sanitize_input(city)
        valid, err = validate_city(city)
        if not valid:
            st.error(err)
        else:
            guard = get_submit_guard()
            lock_key = f"{st.session_state.username}-{city}-{days}"
            if not guard.try_acquire(lock_key):
                st.warning("相同的规划正在进行中，请稍候...")
            else:
                st.session_state._lock_key = lock_key
                st.session_state._recommend_mode = False
                st.session_state.loading = True
                st.session_state.result = None

if st.session_state.loading:
    if st.session_state.get("_recommend_mode"):
        with st.spinner(f"正在根据 ¥{budget}/{days}天/「{preferences}」智能推荐目的地..."):
            from agents.recommend_agent import RecommendAgent
            rec = RecommendAgent()
            result = rec.recommend(budget=budget, days=days, preferences=preferences)
            st.session_state.result = result
    else:
        with st.spinner(f"正在为你规划 {city} {days}日游..."):
            coordinator = TravelCoordinator()
            result = coordinator.plan(
                city=city.strip(),
                days=days,
                budget=budget,
                preferences=preferences,
            )
            st.session_state.result = result

            # 保存到 SQLite
            if st.session_state.username.strip():
                user_id = get_or_create_user(st.session_state.username.strip())
                save_plan(user_id, city.strip(), days, budget, preferences, result)

    # 释放防重复锁
    if "_lock_key" in st.session_state:
        get_submit_guard().release(st.session_state._lock_key)
    st.session_state.loading = False
    st.rerun()

if st.session_state.result:
    st.markdown(st.session_state.result)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 下载旅行计划 (TXT)",
            data=st.session_state.result,
            file_name=f"{city}_{days}日游计划.txt",
            mime="text/plain",
        )
    with col2:
        if st.button("🔄 重新规划", use_container_width=True):
            st.session_state.result = None
            st.rerun()
    with col3:
        st.caption(f"目的地: {city} | {days}天 | 预算: {budget}元")

elif not st.session_state.loading:
    # 欢迎页
    st.info("输入国内城市，本地有资料的秒回，没有的自动联网搜索后生成")

    st.markdown("""
    ### 这个系统做了什么

    1. **行程规划 Agent** → 从知识库检索攻略 → 制定每日行程
    2. **预算分析 Agent** → 查询市场参考价 → 计算总费用
    3. **文化讲解 Agent** → 介绍当地历史文化 → 提醒风俗禁忌
    4. **主控 Agent** → 调度上面三位专家 → 汇总成完整计划

    ### 你学到的核心技术

    | 技术 | 在项目中的体现 |
    |------|--------------|
    | RAG | 攻略文档 → 向量检索 → 增强 LLM 回答 |
    | MCP | JSON-RPC 协议 → 标准化工具接口 |
    | Agent | model + tools + system_prompt = 专业 AI |
    | Agent-Team | 主控调度多个专业 Agent 协作 |
    | Skills | @tool 装饰器 = Agent 的技能卡 |
    """)
