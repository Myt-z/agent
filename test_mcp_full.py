"""
测试 MCP 端到端：启动 Weather Server → Client 连接 → 调用工具
"""
from mcp.client import MCPClient
from mcp.weather_server import get_weather

print("=" * 60)
print("测试1：直接调用 get_weather 函数（不走 MCP）")
print("=" * 60)
print(get_weather("西安", "autumn"))

print("\n" + "=" * 60)
print("测试2：通过 MCP 协议调用（Client → Server 子进程）")
print("=" * 60)

# 启动 weather_server.py 作为子进程
client = MCPClient(["python", "mcp/weather_server.py"])
client.start()

# 列出可用工具
tools = client.list_tools()
print(f"可用工具：{len(tools)} 个")
for t in tools:
    print(f"  - {t['name']}: {t['description']}")

# 调用 get_weather 工具
result = client.call_tool("get_weather", {"city": "西安", "season": "autumn"})
print(f"\n工具返回：{result}")

result2 = client.call_tool("get_weather", {"city": "成都", "season": "summer"})
print(f"工具返回：{result2}")

# 读 stderr（看子进程有没有报错）
if client.process:
    stderr_output = client.process.stderr.read()
    if stderr_output:
        print(f"\n[Server stderr]: {stderr_output}")

client.stop()
print("\nMCP 协议验证通过！")
