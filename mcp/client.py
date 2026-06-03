"""
MCP Client —— 通过子进程启动 MCP Server，发送 JSON-RPC 请求

工作原理：
  1. 用 subprocess.Popen 启动一个 MCP Server 进程
  2. 通过 server 的 stdin 发送 JSON 请求
  3. 通过 server 的 stdout 读取 JSON 响应

这样 Agent 就能通过 MCP 协议调用外部工具了。
"""

import subprocess
import os
import json
from mcp.protocol import JSONRPCRequest, parse_message


class MCPClient:
    """
    MCP 客户端。连接到指定的 MCP Server，调用其工具。

    用法：
      client = MCPClient(["python", "mcp/weather_server.py"])
      client.start()
      tools = client.list_tools()          # 获取可用工具列表
      result = client.call_tool("get_weather", {"city": "西安"})  # 调用工具
      client.stop()
    """

    def __init__(self, command: list[str]):
        """
        command: 启动 MCP Server 的命令，如 ["python", "mcp/weather_server.py"]
        """
        self.command = command
        self.process: subprocess.Popen | None = None
        self._request_id = 0

    def start(self):
        """启动 MCP Server 子进程"""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
        )

    def stop(self):
        """关闭 MCP Server"""
        if self.process:
            self.process.stdin.close()
            self.process.terminate()
            self.process.wait()
            self.process = None

    def _send_request(self, method: str, params: dict | None = None) -> dict:
        """发送一个 JSON-RPC 请求，返回解析后的响应"""
        if not self.process:
            raise RuntimeError("MCP Client 还没启动，先调 start()")

        self._request_id += 1
        request = JSONRPCRequest(
            method=method,
            params=params,
            id=self._request_id,
        )

        # 通过 stdin 发送
        self.process.stdin.write(request.to_json() + "\n")
        self.process.stdin.flush()

        # 通过 stdout 读取响应
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("MCP Server 没有返回响应")

        return parse_message(line)

    def list_tools(self) -> list[dict]:
        """获取 Server 提供的所有工具"""
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> str:
        """
        调用指定工具。

        name: 工具名称
        arguments: 参数字典

        返回: 工具执行结果（字符串）
        """
        response = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

        if "error" in response:
            return f"[MCP 错误] {response['error']['message']}"

        # MCP 协议规定结果在 result.content[].text 里
        content_list = response.get("result", {}).get("content", [])
        if content_list:
            return content_list[0].get("text", "")
        return "工具没有返回内容"
