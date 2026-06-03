"""
知行旅行规划助手 — 命令行入口

用法：
  python main.py --city 西安 --days 3 --budget 3000
  python main.py --city 成都 --days 2 --budget 2000 --preferences 美食+熊猫
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
from agents.coordinator import TravelCoordinator


def main():
    parser = argparse.ArgumentParser(
        description="AI 旅行规划助手 — 基于 LangChain 多 Agent 协作",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --city 西安 --days 3 --budget 3000
  python main.py --city 成都 --days 2 --preferences 美食+看熊猫
        """,
    )
    parser.add_argument("--city", required=True, help="目的地城市（如 西安、成都）")
    parser.add_argument("--days", type=int, default=3, help="游玩天数（默认 3）")
    parser.add_argument("--budget", type=float, default=3000, help="总预算 元（默认 3000）")
    parser.add_argument("--preferences", default="综合体验", help="旅行偏好（默认 综合体验）")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print(f"  知行旅行规划助手")
    print(f"  目的地: {args.city} | 天数: {args.days} | 预算: {args.budget} 元")
    print(f"  偏好: {args.preferences}")
    print("=" * 60)

    coordinator = TravelCoordinator()
    result = coordinator.plan(
        city=args.city,
        days=args.days,
        budget=args.budget,
        preferences=args.preferences,
    )

    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    main()
