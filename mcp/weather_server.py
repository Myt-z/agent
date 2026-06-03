"""
天气 MCP Server —— 基于 MCP 协议的天气查询服务

这个文件展示了如何用 MCPServer 基类创建一个具体的 MCP Server。
数据是 mock 的，重点是理解 MCP 协议流程。

运行方式（独立运行，等待 stdin）：
  python mcp/weather_server.py
"""

import sys
from pathlib import Path

# 确保能找到 mcp 包（从项目根目录运行子进程时）
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import MCPServer

# ========== Mock 天气数据 ==========
WEATHER_DATA = {
    "西安": {"spring": "15-25°C，多云，偶有沙尘", "summer": "30-38°C，炎热干燥",
             "autumn": "12-22°C，秋高气爽，最佳季节", "winter": "-5-5°C，寒冷有霾"},
    "成都": {"spring": "15-25°C，阴雨较多", "summer": "25-33°C，闷热潮湿",
             "autumn": "15-25°C，凉爽宜人", "winter": "3-10°C，阴冷潮湿"},
    "北京": {"spring": "10-22°C，多风", "summer": "25-35°C，炎热",
             "autumn": "10-20°C，秋高气爽", "winter": "-8-5°C，寒冷干燥"},
    "杭州": {"spring": "12-24°C，细雨蒙蒙", "summer": "28-37°C，闷热",
             "autumn": "15-25°C，桂花飘香", "winter": "0-8°C，湿冷"},
    "广州": {"spring": "18-26°C，回南天潮湿", "summer": "28-36°C，高温多雨",
             "autumn": "20-28°C，干燥舒适，最佳季节", "winter": "10-20°C，温暖宜人"},
    "纽约": {"spring": "5-18°C，多雨", "summer": "22-32°C，湿热",
             "autumn": "10-20°C，秋叶最美", "winter": "-5-5°C，大雪"},
    "洛杉矶": {"spring": "13-22°C，阳光充足", "summer": "20-28°C，干燥凉爽",
               "autumn": "15-25°C，舒适", "winter": "8-18°C，温和多雨"},
    "旧金山": {"spring": "10-18°C，多雾", "summer": "12-22°C，凉爽（Mark Twain：最冷的冬天是旧金山的夏天）",
               "autumn": "12-22°C，最佳季节", "winter": "8-15°C，多雨"},
}


def get_weather(city: str, season: str = "spring") -> str:
    """
    查询指定城市和季节的天气。

    city: 城市名（如 西安、成都、北京）
    season: 季节（spring/summer/autumn/winter）
    """
    city_data = WEATHER_DATA.get(city)
    if not city_data:
        return f"暂无 {city} 的天气数据。支持的城市：{'、'.join(WEATHER_DATA.keys())}"

    season_names = {"spring": "春季", "summer": "夏季", "autumn": "秋季", "winter": "冬季"}
    season_cn = season_names.get(season, season)
    weather = city_data.get(season, "暂无该季节数据")

    return f"{city} {season_cn}天气：{weather}"


# ========== 创建并启动 Server ==========
def create_weather_server() -> MCPServer:
    """工厂函数：创建注册好工具的天气 MCP Server"""
    server = MCPServer(name="weather-server", version="1.0")

    server.register_tool(
        name="get_weather",
        handler=get_weather,
        description="查询指定城市在特定季节的天气情况",
        input_schema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名，如 西安、成都、北京、杭州",
                },
                "season": {
                    "type": "string",
                    "enum": ["spring", "summer", "autumn", "winter"],
                    "description": "季节，spring/summer/autumn/winter",
                    "default": "spring",
                },
            },
            "required": ["city"],
        },
    )

    return server


# 如果直接运行这个文件，启动 MCP Server
if __name__ == "__main__":
    # 强制 stdout 为 UTF-8（MCP 协议要求）
    sys.stdout.reconfigure(encoding='utf-8')
    server = create_weather_server()
    print(f"Weather MCP Server 已启动 (name={server.name}, {len(server.tools)} 个工具)", file=sys.stderr, flush=True)
    server.run()
