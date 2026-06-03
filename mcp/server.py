"""
MCP Server 基类 —— stdin/stdout 通信的服务端

工作流程：
  1. 启动后死循环读 stdin（一行一个 JSON）
  2. 收到 "tools/list" → 返回所有注册的工具列表
  3. 收到 "tools/call"  → 找到对应工具 → 执行 → 返回结果
  4. 结果通过 stdout 输出（也是一行一个 JSON）
"""

import sys
import json
from mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MCPTool,
    parse_message,
)


class MCPServer:
    """
    MCP 服务端基类。

    用法：
      server = MCPServer(name="my-server", version="1.0")
      server.register_tool("get_weather", handler_func, schema)
      server.run()  # 阻塞，等待 stdin 输入
    """

    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.tools: dict[str, dict] = {}  # name → {handler, tool}

    def register_tool(
        self,
        name: str,
        handler,
        description: str,
        input_schema: dict | None = None,
    ):
        """注册一个工具。name=工具名, handler=处理函数, description=描述"""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema or {
                "type": "object",
                "properties": {},
                "required": [],
            },
        )
        self.tools[name] = {
            "handler": handler,
            "tool": tool.to_dict(),
        }

    def handle_request(self, request: dict) -> str:
        """处理 JSON-RPC 请求，返回 JSON 响应字符串"""
        method = request.get("method")
        req_id = request.get("id", 1)

        if method == "initialize":
            # MCP 初始化握手：客户端连接后第一个请求
            return JSONRPCResponse(
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version,
                    },
                },
                id=req_id,
            ).to_json()

        elif method == "notifications/initialized":
            # 客户端通知"初始化完成"，不需要回复
            return JSONRPCResponse(result={}, id=req_id).to_json()

        elif method == "ping":
            # 心跳检测
            return JSONRPCResponse(result={}, id=req_id).to_json()

        elif method == "tools/list":
            tools_list = [t["tool"] for t in self.tools.values()]
            return JSONRPCResponse(
                result={"tools": tools_list},
                id=req_id,
            ).to_json()

        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                return JSONRPCError(
                    code=-32601,
                    message=f"工具 '{tool_name}' 不存在",
                    id=req_id,
                ).to_json()

            try:
                handler = self.tools[tool_name]["handler"]
                result_text = handler(**arguments)
                return JSONRPCResponse(
                    result={
                        "content": [
                            {"type": "text", "text": str(result_text)}
                        ]
                    },
                    id=req_id,
                ).to_json()
            except Exception as e:
                return JSONRPCError(
                    code=-32000,
                    message=f"工具执行出错: {str(e)}",
                    id=req_id,
                ).to_json()

        else:
            return JSONRPCError(
                code=-32601,
                message=f"未知方法 '{method}'",
                id=req_id,
            ).to_json()

    def run(self):
        """启动服务端主循环。读 stdin → 处理 → 输出到 stdout。会阻塞直到 stdin 关闭。"""
        while True:
            line = sys.stdin.readline()
            if not line:
                break  # stdin 关闭，退出
            line = line.strip()
            if not line:
                continue
            try:
                request = parse_message(line)
                response = self.handle_request(request)
                print(response, flush=True)
            except Exception as e:
                error_response = JSONRPCError(
                    code=-32700,
                    message=f"解析请求失败: {str(e)}",
                ).to_json()
                print(error_response, flush=True)
