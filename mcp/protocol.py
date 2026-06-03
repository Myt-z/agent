"""
MCP 协议核心 —— JSON-RPC 2.0 消息类型

MCP 的本质就是 JSON-RPC 2.0 over stdio。
服务端和客户端通过标准输入(stdin)和标准输出(stdout)交换 JSON 消息。

三种消息：
  1. Request  → 客户端发给服务端（"帮我做这件事"）
  2. Response → 服务端回复客户端（"做完了，结果在这"）
  3. Error    → 服务端回复客户端（"做不了，原因是..."）
"""

from dataclasses import dataclass, field
import json


@dataclass
class JSONRPCRequest:
    """客户端发送的请求"""
    method: str
    params: dict | None = None
    jsonrpc: str = "2.0"
    id: int = 1

    def to_json(self) -> str:
        """序列化成 JSON 字符串，通过 stdout 发送"""
        return json.dumps({
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params or {},
            "id": self.id,
        }, ensure_ascii=False)


@dataclass
class JSONRPCResponse:
    """服务端成功的回复"""
    result: dict
    id: int = 1
    jsonrpc: str = "2.0"

    def to_json(self) -> str:
        return json.dumps({
            "jsonrpc": self.jsonrpc,
            "result": self.result,
            "id": self.id,
        }, ensure_ascii=False)


@dataclass
class JSONRPCError:
    """服务端失败的回复"""
    code: int
    message: str
    id: int = 1
    jsonrpc: str = "2.0"

    def to_json(self) -> str:
        return json.dumps({
            "jsonrpc": self.jsonrpc,
            "error": {"code": self.code, "message": self.message},
            "id": self.id,
        }, ensure_ascii=False)


def parse_message(line: str) -> dict:
    """解析一行 JSON → Python dict"""
    return json.loads(line)


@dataclass
class MCPTool:
    """描述一个工具"""
    name: str
    description: str
    input_schema: dict = field(default_factory=lambda: {
        "type": "object",
        "properties": {},
        "required": [],
    })

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }
