"""
性能实验：有索引 vs 无索引的等值查询耗时对比。

实验设计：
1. 加载 10 万行测试数据
2. 对某一列（如 ID）构建哈希索引
3. 执行多次等值查询，分别记录有/无索引的耗时
4. 计算平均耗时和加速比
"""

import sys
import time
import random
from pathlib import Path

# 确保能找到 src 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db_engine.csv_loader import load_csv
from db_engine.hash_index import HashIndex, index_lookup


def run_experiment(csv_path: str, num_trials: int = 50):
    """运行索引性能对比实验"""
    print("=" * 60)
    print("哈希索引性能对比实验")
    print("=" * 60)

    # 加载数据
    print(f"\n[1/4] 加载数据: {csv_path}")
    start = time.time()
    table = load_csv(csv_path)
    load_time = time.time() - start
    print(f"  完成！{table.num_rows:,} 行, {table.num_columns} 列, 耗时 {load_time:.2f}s")

    # 选择测试列（优先选 ID/编号列，如果存在）
    test_column = "ID" if "ID" in table.column_names else table.column_names[0]
    print(f"\n[2/4] 对列 '{test_column}' 构建哈希索引...")
    start = time.time()
    index = HashIndex(table, test_column)
    build_time = time.time() - start
    print(f"  索引大小: {index.size():,} 个唯一值, 构建耗时 {build_time:.4f}s")
    print(f"  估算内存: {index.memory_estimate()}")

    # 准备测试查询值（随机选择）
    col_idx = table.get_column_index(test_column)
    sample_values = []
    for _ in range(num_trials):
        row_idx = random.randint(0, table.num_rows - 1)
        sample_values.append(table.rows[row_idx][col_idx])

    print(f"\n[3/4] 执行 {num_trials} 次等值查询对比...")

    # ====== 有索引 ======
    index_times = []
    for val in sample_values:
        start = time.perf_counter()
        result = index_lookup(table, test_column, val, index=index)
        elapsed = time.perf_counter() - start
        index_times.append(elapsed)
        # 验证结果正确性
        assert len(result.rows) > 0, f"索引查找返回空: {val}"

    avg_index = (sum(index_times) / len(index_times)) * 1000  # 转 ms
    min_index = min(index_times) * 1000
    max_index = max(index_times) * 1000

    print(f"\n  >> 有索引 (Hash Index):")
    print(f"     平均耗时: {avg_index:.4f} ms")
    print(f"     最小耗时: {min_index:.4f} ms")
    print(f"     最大耗时: {max_index:.4f} ms")

    # ====== 无索引（全表扫描） ======
    scan_times = []
    for val in sample_values:
        start = time.perf_counter()
        result = index_lookup(table, test_column, val, index=None)
        elapsed = time.perf_counter() - start
        scan_times.append(elapsed)
        assert len(result.rows) > 0, f"全表扫描返回空: {val}"

    avg_scan = (sum(scan_times) / len(scan_times)) * 1000
    min_scan = min(scan_times) * 1000
    max_scan = max(scan_times) * 1000

    print(f"\n  >> 无索引 (全表扫描 Full Scan):")
    print(f"     平均耗时: {avg_scan:.4f} ms")
    print(f"     最小耗时: {min_scan:.4f} ms")
    print(f"     最大耗时: {max_scan:.4f} ms")

    # 加速比
    speedup = avg_scan / avg_index if avg_index > 0 else float('inf')
    print(f"\n[4/4] 结论")
    print(f"  ** 加速比: {speedup:.1f}x")
    print(f"  {'=' * 40}")
    print(f"  有索引比无索引快了约 {speedup:.0f} 倍！")
    if speedup > 10:
        print(f"  这验证了哈希索引 O(1) 查找 vs 全表扫描 O(n) 的理论差异。")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/large_test.csv"
    trials = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    run_experiment(csv_path, trials)
