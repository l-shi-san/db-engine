"""
NL2SQL 测试 —— 12 个自然语言转 SQL 测试用例

题目要求：提供至少 10 个测试用例，展示转换结果与执行结果。
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# 切换工作目录到项目根目录（确保 test_data.csv 能被找到）
os.chdir(Path(__file__).resolve().parent.parent)

from db_engine.nl2sql import NL2SQLEngine, get_test_cases
from db_engine.engine import Engine


def test_nl2sql_translation():
    """测试 12 个 NL2SQL 转换是否都能生成 SQL"""
    engine = NL2SQLEngine(table_name="test_data.csv")
    cases = get_test_cases()
    for case in cases:
        sql = engine.translate(case['nl'])
        assert sql and len(sql) > 0, f"转换失败: {case['nl']}"
        assert sql.upper().startswith("SELECT"), f"生成的 SQL 必须以 SELECT 开头: {sql}"
    print(f"  ✓ {len(cases)} 个 NL2SQL 转换测试全部通过")


def test_nl2sql_execution():
    """测试 NL2SQL 生成的 SQL 能否在引擎中实际执行"""
    engine = NL2SQLEngine(table_name="test_data.csv")
    db_engine = Engine()

    test_queries = [
        ("查询所有数据", "SELECT * FROM test_data.csv"),
        ("查询年龄大于20的数据", "SELECT * FROM test_data.csv WHERE Age > 20"),
        ("按分数降序排列", "SELECT * FROM test_data.csv ORDER BY Score DESC"),
    ]

    for nl, _ in test_queries:
        sql = engine.translate(nl)
        # 替换表名
        sql = sql.replace("FROM data", "FROM test_data.csv")
        try:
            result = db_engine.execute(sql)
            assert result is not None
        except Exception as e:
            print(f"  ✗ 执行失败: {sql} → {e}")
            raise
    print("  ✓ NL2SQL 生成的 SQL 可执行验证通过")


def run_full_test():
    """运行完整的 NL2SQL 测试，展示 12 个用例的转换和执行结果"""
    print("=" * 70)
    print("NL2SQL 测试报告（12 个用例）")
    print("=" * 70)

    engine = NL2SQLEngine(table_name="test_data.csv")
    db_engine = Engine()

    cases = get_test_cases()
    for i, case in enumerate(cases, 1):
        nl = case['nl']
        description = case['description']

        # 转换为 SQL
        sql = engine.translate(nl)
        # 替换表名
        sql_exec = sql.replace("FROM data", "FROM test_data.csv")

        # 执行
        try:
            result = db_engine.execute(sql_exec)
            if isinstance(result, list):
                row_count = len(result)
                status = "✓"
            else:
                row_count = result.num_rows if hasattr(result, 'num_rows') else '?'
                status = "✓"
        except Exception as e:
            result = None
            row_count = f"错误: {e}"
            status = "✗"

        print(f"\n[{i}] {description}  {status}")
        print(f"    自然语言: {nl}")
        print(f"    生成 SQL: {sql}")
        print(f"    执行结果: {row_count} 行")
        if isinstance(result, list) and len(result) <= 5:
            for row in result:
                print(f"      {row}")

    print(f"\n{'=' * 70}")
    print("测试完成：12 个 NL2SQL 用例全部展示")
    print("=" * 70)


if __name__ == "__main__":
    test_nl2sql_translation()
    test_nl2sql_execution()
    print("\n" + "=" * 50)
    run_full_test()
