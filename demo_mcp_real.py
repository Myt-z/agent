"""
Phase 5：MCP 真实对接 —— FastMCP vs 手写版本的对比

这个文件展示三种 MCP 写法的对比，帮你理解从"手写协议"
到"用现成框架"的进化过程。
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("""
================================================================
  MCP 学习总结：三个层次
================================================================

Level 1: 手写协议 (你写过的 protocol.py / server.py / client.py)
──────────────────────────────────────────────────────────────
  from mcp.server import MCPServer
  server = MCPServer(name="weather-server", version="1.0")
  server.register_tool(
      name="get_weather",
      handler=lambda city, season: f"天气：{city}...",
      description="查询天气",
      input_schema={"type":"object", "properties":{...}},
  )
  server.run()  # 死循环读 stdin → 处理 → stdout

  你写了 ~150 行，理解了 MCP = JSON-RPC 2.0 over stdio
  核心方法：initialize, tools/list, tools/call, ping


Level 2: 官方 FastMCP (pip install mcp)
──────────────────────────────────────────────────────────────
  from mcp.server.fastmcp import FastMCP

  weather_mcp = FastMCP("weather-server")

  @weather_mcp.tool()
  def get_weather(city: str, season: str = "spring") -> str:
      '''查询指定城市在特定季节的天气情况。'''
      return f"{city} 天气：..."

  weather_mcp.run(transport="stdio")

  30 行搞定！@mcp.tool() 自动把函数签名 → JSON Schema
  FastMCP 自动处理整个协议栈


Level 3: LangChain 对接 (langchain-mcp-adapters)
──────────────────────────────────────────────────────────────
  from langchain_mcp_adapters.client import MultiServerMCPClient

  client = MultiServerMCPClient({
      "weather": {
          "transport": "stdio",
          "command": "python",
          "args": ["weather_server.py"],
      }
  })
  tools = await client.get_tools()    # 自动发现 MCP 工具
  agent = create_agent(model, tools)   # 插进 LangChain Agent

  MCP Server 的工具 → LangChain Tool → Agent 直接调用


================================================================
  你现在的位置
================================================================

  ✅ Level 1：理解了 MCP 协议本质
  ✅ 看到了 Level 2 和 3 的代码模式
  📋 下一步：用 FastMCP 重写 weather_server.py（选做，5 分钟）

  验证手写 MCP：python test_mcp_simple.py
  验证 Agent-Team：python main.py --city 西安 --days 2 --budget 2000
================================================================
""")
