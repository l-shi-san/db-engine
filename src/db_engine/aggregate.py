"""
聚合函数 —— COUNT, SUM, AVG, MAX, MIN。

聚合（Aggregation）是数据库"汇总"数据的能力。
它不是对每一行做计算，而是把多行数据"压缩"成一个结果。

例子：
    SELECT AVG(Age) FROM students
    → 把所有学生的年龄加起来，除以人数，得到平均年龄
    
这就是关系代数中的 γ（聚合）操作。
"""

from __future__ import annotations

from typing import Any

from .table import Table
from .parser import AggFunction


def execute_aggregate(table: Table, agg_func: AggFunction) -> Any:
    """执行一个聚合函数调用"""
    column = agg_func.column

    if column == "*":
        # COUNT(*) 计数所有行
        if agg_func.name == "COUNT":
            return len(table.rows)
        raise ValueError(f"不支持对 * 使用 {agg_func.name}")

    # 获取列的值列表
    try:
        col_idx = table.get_column_index(column)
    except ValueError:
        raise ValueError(f"列 '{column}' 不存在")

    values = [row[col_idx] for row in table.rows if row[col_idx] is not None]

    if not values:
        if agg_func.name in ("SUM", "AVG"):
            return 0
        elif agg_func.name == "COUNT":
            return 0
        elif agg_func.name == "MAX":
            return None
        elif agg_func.name == "MIN":
            return None

    name = agg_func.name

    if name == "COUNT":
        return len(values)

    elif name == "SUM":
        return _ensure_numeric_sum(values)

    elif name == "AVG":
        nums = _ensure_numeric(values)
        return sum(nums) / len(nums)

    elif name == "MAX":
        return max(values)

    elif name == "MIN":
        return min(values)

    else:
        raise ValueError(f"不支持的聚合函数: {name}")


def _ensure_numeric(values: list) -> list[float | int]:
    """确保所有值都是数字类型"""
    numeric = []
    for v in values:
        if isinstance(v, (int, float)):
            numeric.append(v)
        else:
            try:
                numeric.append(float(v))
            except (ValueError, TypeError):
                raise ValueError(f"聚合函数要求数字类型，但遇到了: {v} ({type(v)})")
    return numeric


def _ensure_numeric_sum(values: list) -> float | int:
    """计算数值和"""
    return sum(_ensure_numeric(values))


def has_aggregate(items: list) -> bool:
    """检查 SELECT 项中是否包含聚合函数"""
    from .parser import AggFunction
    return any(isinstance(item, AggFunction) for item in items)
