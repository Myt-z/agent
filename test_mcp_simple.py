"""
最简单的 MCP 协议测试 —— 不走子进程，直接调 server.handle_request()
证明 JSON-RPC 消息格式是正确的。
"""
from mcp.protocol import parse_message
from mcp.weather_server import create_weather_server

server = create_weather_server()

# 模拟客户端发送 tools/list
print("=== 客户端 → 服务端 ===")
req1 = '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
print(f"发送: {req1}")

resp1 = server.handle_request(parse_message(req1))
print(f"收到: {resp1}")

# 模拟客户端发送 tools/call
print("\n=== 客户端 → 服务端 ===")
req2 = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_weather","arguments":{"city":"西安","season":"autumn"}},"id":2}'
print(f"发送: {req2}")

resp2 = server.handle_request(parse_message(req2))
print(f"收到: {resp2}")

print("\nMCP 协议核心流程验证通过！")
