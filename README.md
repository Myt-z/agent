# 知行旅行规划助手

基于 LangChain 多 Agent 协作的 AI 旅行规划系统。输入国内城市和预算，主控 Agent 自动调度三位 AI 专家（行程规划师、预算分析师、文化讲解员）协作生成完整旅行计划。

## 快速开始

### Docker（推荐，跨平台一键部署）

```bash
cp .env.example .env   # 编辑 .env 填入 API Key
docker-compose up -d    # 浏览器打开 http://localhost:8501
```

### 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 .env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
APP_ENV=dev

# 3. 启动
streamlit run app.py
# 或 Windows 双击 start.bat
```

### 环境切换

```bash
APP_ENV=test  pytest tests/ -v    # 沙盒测试，¥0 成本
APP_ENV=dev   streamlit run app.py  # 开发，调试日志
APP_ENV=prod  docker-compose up -d  # 生产，降级链+错误日志
```

## 项目结构

```
travel-planner/
├── app.py                        # Streamlit 浏览器界面
├── main.py                       # 命令行入口：python main.py --city 西安 --days 3
├── start.bat                     # Windows 一键启动
│
├── agents/                       # Agent 层
│   ├── coordinator.py            # 主控调度 Agent（Agent-Team 编排）
│   ├── itinerary_agent.py        # 行程规划 Agent（RAG 检索 + 联网搜索）
│   ├── budget_agent.py           # 预算分析 Agent（@tool 工具调用）
│   └── culture_agent.py          # 文化讲解 Agent（RAG 检索）
│
├── rag/                          # RAG 知识库层
│   ├── knowledge_store.py        # 向量库：建库 / 检索 / 时效性管理
│   ├── data/                     # 本地知识文档
│   │   ├── xian-guide.txt        # 西安攻略
│   │   ├── guangzhou_guide.txt   # 广州攻略
│   │   └── culture_tips.txt      # 旅行文化常识
│   └── chroma_db/                # ChromaDB 持久化（自动生成）
│
├── mcp/                          # MCP 协议层（手写实现）
│   ├── protocol.py               # JSON-RPC 2.0 消息类型
│   ├── server.py                 # MCP Server 基类（stdin/stdout）
│   ├── client.py                 # MCP Client（子进程通信）
│   └── weather_server.py         # 天气 MCP Server 实例
│
├── tools/                        # Skills 工具层
│   ├── travel_tools.py           # @tool：预算计算 / 参考价查询
│   └── search_tools.py           # @tool：DuckDuckGo 联网搜索
│
├── db/                           # SQLite 数据库层
│   ├── database.py               # 用户 / 计划存储 / 热门排行
│   └── travel_planner.db         # SQLite 数据库文件（自动生成）
│
└── debug/                        # 调试工具
    └── tracer.py                 # LLM 调用追踪器
```

## 核心架构

```
用户输入 "西安 3天 3000元"
        │
        ▼
┌──────────────────┐
│  主控 Agent       │  Agent-Team 调度
│  coordinator.py   │
└──┬──────┬──────┬─┘
   │      │      │
   ▼      ▼      ▼
行程规划  预算分析  文化讲解
Agent    Agent    Agent
(RAG)    (Tools)  (RAG)
   │      │      │
   └──────┼──────┘
          ▼
┌──────────────────┐
│   知识检索层       │
│  优先本地 ChromaDB │ → 低于阈值 → DuckDuckGo 联网
│  结果自动入库      │ → 30 天过期自动刷新
└──────────────────┘
          │
          ▼
┌──────────────────┐
│   SQLite          │
│   保存计划 / 历史  │
└──────────────────┘
```

## 技术栈

| 层 | 技术 | 用途 |
|---|---|---|
| Agent 框架 | LangChain 1.3（create_agent） | 多 Agent 编排 |
| 大模型 | DeepSeek API（deepseek-chat） | 工具调用 + 文本生成 |
| 向量数据库 | ChromaDB | 语义检索 |
| Embedding | all-MiniLM-L6-v2（本地 CPU） | 文本向量化 |
| 关系数据库 | SQLite（WAL 模式） | 用户 + 计划存储 |
| 搜索引擎 | DuckDuckGo（ddgs） | 联网兜底 |
| 协议 | MCP（手写 JSON-RPC） | 工具标准化通信 |
| 前端 | Streamlit | 浏览器界面 |

## 学习目标

| 概念 | 代码位置 | 说明 |
|------|---------|------|
| RAG | `rag/knowledge_store.py` | 文档切块 → 向量化 → 语义检索 → 时效性管理 |
| MCP 协议 | `mcp/protocol.py` + `server.py` + `client.py` | JSON-RPC 2.0 over stdio 手写实现 |
| Agent | `agents/itinerary_agent.py` 等 | model + tools + system_prompt = 专业 Agent |
| Agent-Team | `agents/coordinator.py` | 子 Agent 包装为 @tool，主控按 SOP 调度 |
| Agent-Skills | system_prompt + @tool | system_prompt 定义人设，@tool 定义技能卡 |
| Skills | `tools/travel_tools.py` | @tool 装饰器 = 普通函数 → Agent 可用工具 |
| 数据库 | `db/database.py` | SQLite 存储用户、计划、热门排行 |

## 命令行用法

```bash
# 命令行规划
python main.py --city 西安 --days 3 --budget 3000 --preferences 历史文化

# 一键测试所有模块
python test_all.py
# 或双击 test_all.bat

# 单独测试
python test_rag.py          # RAG 知识库
python test_mcp_simple.py   # MCP 协议
python test_hybrid.py       # 混合搜索
```

## 配置说明

`.env` 文件：

```
DEEPSEEK_API_KEY=sk-your-key    # DeepSeek API Key（必填）
DEEPSEEK_BASE_URL=https://api.deepseek.com
HF_ENDPOINT=https://hf-mirror.com  # HuggingFace 国内镜像
```
