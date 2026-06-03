"""
MCP 真实对接演示 —— 用 langchain-mcp-adapters 连接 MCP Server

你手写的 protocol/server/client 让你理解了 MCP 的原理。
这个文件展示：有了标准 MCP 协议后，LangChain 怎么一键对接。

流程：
  1. MultiServerMCPClient 启动 weather_server.py 作为子进程
  2. 自动发现 Server 提供的所有工具
  3. 把 MCP 工具转成 LangChain @tool → 插进 Agent
"""

import sys
from pathlib import Path

# 注意：langchain-mcp-adapters 依赖官方 mcp 包（pip install mcp）
# 我们手写的 mcp/ 目录会挡住它，所以先把手写的路径拿掉
_project_root = str(Path(__file__).parent.parent)
if _project_root in sys.path:
    sys.path.remove(_project_root)

import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# 恢复路径（以便后续可能需要导入项目模块）
sys.path.insert(0, _project_root)


def demo_mcp_with_agent():
    """
    演示：连接 MCP Server → 获取工具 → 创建 Agent → 调用
    """

    print("=" * 60)
    print("  MCP 真实对接演示")
    print("=" * 60)

    # 第1步：配置 MCP Server
    # 用 langchain-mcp-adapters 的 MultiServerMCPClient
    # 它会自动启动子进程、处理 JSON-RPC 通信、解析工具列表
    print("\n[1] 连接 weather MCP Server...")

    mcp_config = {
        "weather": {
            "command": "python",
            "args": ["mcp/weather_server.py"],
            "transport": "stdio",
        }
    }

    client = MultiServerMCPClient(mcp_config)

    # 第2步：获取 MCP Server 提供的工具
    # get_tools() 会把 MCP 工具自动转成 LangChain Tool 对象
    tools = client.get_tools()
    print(f"[2] 从 MCP Server 获取到 {len(tools)} 个工具：")
    for t in tools:
        print(f"    - {t.name}: {t.description[:60]}...")

    # 第3步：创建一个带 MCP 工具的 Agent
    print("\n[3] 创建 Agent（绑定 MCP 工具）...")

    model = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
    )

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="""你是一个旅行天气顾问。
当用户询问天气时，使用 get_weather 工具查询。
回答要简洁，直接给出天气信息和建议。""",
    )

    # 第4步：测试
    print("\n[4] 测试 Agent 调用 MCP 工具...")
    test_queries = [
        "西安秋天天气怎么样？适合旅游吗？",
        "成都夏天热不热？",
    ]

    for q in test_queries:
        print(f"\n{'─' * 40}")
        print(f"  用户: {q}")
        result = agent.invoke({"messages": [{"role": "user", "content": q}]})
        answer = result["messages"][-1].content
        print(f"  AI: {answer[:200]}...")

    print("\n" + "=" * 60)
    print("  MCP 对接完成！")
    print("=" * 60)
    print("""
关键理解：
  你手写的 protocol.py/server.py/client.py = 理解 MCP 原理
  langchain-mcp-adapters = 自动处理这些底层细节

  标准协议的好处：
  - 任何语言的 MCP Server 都能对接（Python/Node/Go...)
  - Agent 不用关心工具是用什么技术实现的
  - 换一个 MCP Server 就像换一个 USB 设备——接口统一，即插即用
""")


if __name__ == "__main__":
    demo_mcp_with_agent()
