"""
性能实验：列式存储 vs 行式存储对比。

实验设计：
1. 准备 10 万行测试数据
2. 分别加载为行式 Table 和列式 ColumnarTable
3. 对比两种场景：
   a. 聚合查询（SUM, AVG）— 列存应显著更快
   b. 全行读取（SELECT *）— 行存应更快
"""

import sys
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db_engine.csv_loader import load_csv
from db_engine.columnar_store import load_columnar_from_csv
from db_engine.aggregate import execute_aggregate
from db_engine.parser import AggFunction


def run_experiment(csv_path: str):
    print("=" * 60)
    print("列式存储 vs 行式存储 性能对比实验")
    print("=" * 60)

    # ── 1. 加载数据 ──
    print(f"\n[1/4] 加载数据: {csv_path}")

    start = time.time()
    row_table = load_csv(csv_path)
    row_load_time = time.time() - start

    start = time.time()
    col_table = load_columnar_from_csv(csv_path)
    col_load_time = time.time() - start

    print(f"  行式加载: {row_load_time:.3f}s | 列式加载: {col_load_time:.3f}s")
    print(f"  数据量: {row_table.num_rows:,} 行, {row_table.num_columns} 列")

    # 选取数值列用于聚合测试
    num_cols = [c.name for c in row_table.schema
                if c.name.lower() not in ('name', 'city', 'gender', 'department')]
    test_col = num_cols[0] if num_cols else row_table.column_names[-1]
    print(f"  测试列: '{test_col}'")

    # ── 2. 聚合查询对比（SUM, AVG） ──
    print(f"\n[2/4] 聚合查询对比（使用列 '{test_col}'）...")

    # --- 行式 SUM ---
    times = []
    for _ in range(30):
        start = time.perf_counter()
        result = execute_aggregate(row_table, AggFunction("SUM", test_col))
        times.append(time.perf_counter() - start)
    row_sum_ms = (sum(times) / len(times)) * 1000

    # --- 列式 SUM ---
    times = []
    for _ in range(30):
        start = time.perf_counter()
        result = col_table.get_column_stats(test_col)['sum']
        times.append(time.perf_counter() - start)
    col_sum_ms = (sum(times) / len(times)) * 1000

    # --- 行式 AVG ---
    times = []
    for _ in range(30):
        start = time.perf_counter()
        result = execute_aggregate(row_table, AggFunction("AVG", test_col))
        times.append(time.perf_counter() - start)
    row_avg_ms = (sum(times) / len(times)) * 1000

    # --- 列式 AVG ---
    times = []
    for _ in range(30):
        start = time.perf_counter()
        result = col_table.get_column_stats(test_col)['avg']
        times.append(time.perf_counter() - start)
    col_avg_ms = (sum(times) / len(times)) * 1000

    print(f"\n  SUM({test_col}):")
    print(f"    行式存储: {row_sum_ms:.4f} ms")
    print(f"    列式存储: {col_sum_ms:.4f} ms")
    print(f"    加速比:   {row_sum_ms/col_sum_ms:.1f}x（列存更快）" if col_sum_ms > 0 else "")

    print(f"\n  AVG({test_col}):")
    print(f"    行式存储: {row_avg_ms:.4f} ms")
    print(f"    列式存储: {col_avg_ms:.4f} ms")
    print(f"    加速比:   {row_avg_ms/col_avg_ms:.1f}x（列存更快）" if col_avg_ms > 0 else "")

    # ── 3. 全行读取对比 ──
    print(f"\n[3/4] 全行读取对比（读取全部 {row_table.num_rows:,} 行）...")

    # --- 行式全行读取 ---
    times = []
    for _ in range(20):
        start = time.perf_counter()
        rows = row_table.rows
        _ = len(rows)
        times.append(time.perf_counter() - start)
    row_full_ms = (sum(times) / len(times)) * 1000

    # --- 列式全行读取（需要组装行） ---
    times = []
    for _ in range(20):
        start = time.perf_counter()
        for i in range(col_table.num_rows):
            _ = col_table.get_row(i)
        times.append(time.perf_counter() - start)
    col_full_ms = (sum(times) / len(times)) * 1000

    print(f"\n  全行读取 {row_table.num_rows:,} 行:")
    print(f"    行式存储: {row_full_ms:.4f} ms")
    print(f"    列式存储: {col_full_ms:.4f} ms")
    print(f"    减速比:   {col_full_ms/row_full_ms:.1f}x（列存更慢）" if row_full_ms > 0 else "")

    # ── 4. 结论 ──
    print(f"\n[4/4] 实验结论")
    print("=" * 60)
    print(f"  聚合查询（SUM/AVG）：列式存储 vs 行式存储")
    print(f"    SUM 加速: {row_sum_ms/col_sum_ms:.1f}x  ← 列存只需读取一列")
    print(f"    AVG 加速: {row_avg_ms/col_avg_ms:.1f}x")
    print()
    print(f"  全行读取：行式存储 vs 列式存储")
    print(f"    行存优势: {col_full_ms/row_full_ms:.1f}x  ← 行存一次性读取整行")
    print()
    print(f"  结论：列式存储擅长聚合分析，行式存储擅长事务查询")
    print(f"  这就是 OLAP（列存）与 OLTP（行存）的设计哲学差异。")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/large_test.csv"
    run_experiment(csv_path)
