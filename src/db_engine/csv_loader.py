"""
CSV 加载器 —— 从 CSV 文件读取数据并转换为内存中的 Table。

这是数据库的"导入"功能。CSV（逗号分隔值）是最通用的数据交换格式。
数据库引擎需要能读取 CSV 文件，推断每列的数据类型，然后存入内存。
"""

from __future__ import annotations

import csv
from pathlib import Path

from .table import Column, Table
from .types import infer_type, cast_value


def load_csv(filepath: str | Path, has_header: bool = True,
             delimiter: str = ",") -> Table:
    """从 CSV 文件加载数据到 Table。

    步骤：
    1. 读取 CSV 文件的所有行
    2. 推断每列的数据类型
    3. 将字符串值转换为对应的 Python 类型
    4. 构建 Table 对象返回

    这就是数据库的"数据导入"过程 —— ETL 的第一步（Extract）。
    """
    filepath = Path(filepath)

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=delimiter)
        raw_rows = list(reader)

    if not raw_rows:
        raise ValueError(f"CSV 文件为空: {filepath}")

    # 提取表头和数据行
    if has_header:
        column_names = raw_rows[0]
        data_rows = raw_rows[1:]
    else:
        column_names = [f"col{i}" for i in range(len(raw_rows[0]))]
        data_rows = raw_rows

    if not data_rows:
        # 只有表头没有数据
        schema = [Column(name, infer_type([])) for name in column_names]
        return Table(schema=schema, rows=[])

    # 转置：按列提取所有值用于类型推断
    num_cols = len(column_names)
    columns_values: list[list[str]] = [[] for _ in range(num_cols)]

    for row in data_rows:
        # 处理行中列数不足的情况
        padded = row[:num_cols] + [""] * (num_cols - len(row))
        for i, val in enumerate(padded):
            columns_values[i].append(val)

    # 推断每列的类型
    col_types = [infer_type(vals) for vals in columns_values]

    # 构建 schema
    schema = [Column(name, col_type)
              for name, col_type in zip(column_names, col_types)]

    # 类型转换：字符串 → Python 原生类型
    typed_rows = []
    for row in data_rows:
        padded = row[:num_cols] + [""] * (num_cols - len(row))
        typed_row = [cast_value(val, col_types[i])
                     for i, val in enumerate(padded)]
        typed_rows.append(typed_row)

    return Table(schema=schema, rows=typed_rows)
