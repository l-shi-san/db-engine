"""
CLI 交互界面 —— 命令行数据库终端。

提供两种使用模式：
1. REPL 模式：交互式输入查询
2. 单次执行模式：python -m db_engine.cli "SELECT * FROM data.csv"
"""

from __future__ import annotations

import sys
from pathlib import Path

# 同时支持 python -m db_engine.cli 和直接运行 cli.py
if __name__ == "__main__" and __package__ is None:
    __package__ = "db_engine"
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .engine import Engine


def format_result(results: list[dict], max_rows: int = 30) -> str:
    """格式化查询结果为表格文本"""
    if not results:
        return "(空结果)"

    # 获取所有列名
    columns = list(results[0].keys())

    # 计算每列宽度
    col_widths = {}
    for col in columns:
        # 列名宽度
        width = len(str(col))
        for row in results:
            val = str(row.get(col, ""))
            width = max(width, len(val))
        col_widths[col] = min(width, 80)  # 限制最大宽度

    # 构建表头
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    sep = "-" * len(header)

    lines = [header, sep]

    # 数据行
    for i, row in enumerate(results):
        if i >= max_rows:
            lines.append(f"... 还有 {len(results) - max_rows} 行")
            break
        line = " | ".join(
            str(row.get(col, "")).ljust(col_widths[col]) for col in columns
        )
        lines.append(line)

    lines.append(f"\n共 {len(results)} 行，{len(columns)} 列")

    return "\n".join(lines)


def run_repl():
    """交互式 REPL 模式"""
    engine = Engine()
    print("╔══════════════════════════════════════════╗")
    print("║    轻量级数据库引擎 - DB Engine         ║")
    print("╠══════════════════════════════════════════╣")
    print("║  输入 SQL 查询，输入 QUIT 退出          ║")
    print("║  示例:                                   ║")
    print("║    SELECT * FROM data.csv               ║")
    print("║    SELECT Name, Age FROM data.csv        ║")
    print("║      WHERE Age > 20 ORDER BY Age DESC   ║")
    print("║    SELECT COUNT(*), AVG(Age) FROM data   ║")
    print("╚══════════════════════════════════════════╝")

    while True:
        try:
            sql = input("\n>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not sql:
            continue

        if sql.upper() in ("QUIT", "EXIT", "Q"):
            print("再见！")
            break

        try:
            result = engine.execute(sql)
            if isinstance(result, list):
                print(format_result(result))
            else:
                print(result.display())
        except Exception as e:
            print(f"错误: {e}")


def main():
    """入口函数"""
    if len(sys.argv) > 1:
        # 单条查询模式
        engine = Engine()
        sql = " ".join(sys.argv[1:])
        try:
            result = engine.execute(sql)
            if isinstance(result, list):
                print(format_result(result))
            else:
                print(result.display())
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)
    else:
        # REPL 模式
        run_repl()


if __name__ == "__main__":
    main()
