"""
生成大 CSV 测试文件（10 万行+）用于性能对比实验。
"""
import csv
import random
import time
from pathlib import Path

OUTPUT = Path("data") / "large_test.csv"
NUM_ROWS = 100_000
NAMES = ["Tom", "Amy", "Bob", "Alice", "Charlie", "Diana", "Eve", "Frank",
         "Grace", "Hank", "Ivy", "Jack", "Kate", "Leo", "Mia", "Noah"]
CITIES = ["NYC", "LA", "Chicago", "Houston", "Phoenix", "Philadelphia",
          "San Antonio", "San Diego", "Dallas", "San Jose"]


def generate():
    Path("data").mkdir(exist_ok=True)

    print(f"正在生成 {NUM_ROWS:,} 行测试数据...")
    start = time.time()

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Age", "City", "Score"])

        for i in range(NUM_ROWS):
            writer.writerow([
                i + 1,
                random.choice(NAMES),
                random.randint(18, 60),
                random.choice(CITIES),
                round(random.uniform(50.0, 100.0), 1),
            ])

    elapsed = time.time() - start
    file_size = OUTPUT.stat().st_size / 1024 / 1024
    print(f"完成！文件: {OUTPUT}")
    print(f"行数: {NUM_ROWS:,}，大小: {file_size:.1f} MB，耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    generate()
