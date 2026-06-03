from mcp.protocol import JSONRPCRequest, JSONRPCResponse, MCPTool

# 测试1：构造一个请求
r = JSONRPCRequest(method="tools/list")
print("请求消息：", r.to_json())

# 测试2：构造一个工具定义
t = MCPTool(name="get_weather", description="查天气")
print("工具定义：", t.to_dict())
