"""
条件过滤引擎 —— 根据 WHERE 条件筛选数据行。

这是数据库"选择"（Selection）操作的实现。
对每一行，判断它是否满足 WHERE 条件，满足则保留，不满足则过滤掉。

条件判断树示例：
    WHERE Age > 18 AND City = 'NYC'
    
    会构建成：
        LogicalAnd
        ├── Comparison(Age, >, 18)
        └── Comparison(City, =, 'NYC')
    
    判断时从叶子节点向上递归计算。
"""

from __future__ import annotations

from .table import Table
from .parser import (
    Condition, Comparison, LogicalAnd, LogicalOr,
    ColumnRef, Literal, Expr
)


def evaluate_condition(row: list, column_names: list[str],
                       condition: Condition) -> bool:
    """对一行数据评估条件是否成立。

    这是数据库"谓词求值"（Predicate Evaluation）的核心逻辑。
    对每一行，递归计算条件表达式树的结果（True 或 False）。
    """
    if isinstance(condition, Comparison):
        return _eval_comparison(row, column_names, condition)
    elif isinstance(condition, LogicalAnd):
        return (evaluate_condition(row, column_names, condition.left) and
                evaluate_condition(row, column_names, condition.right))
    elif isinstance(condition, LogicalOr):
        return (evaluate_condition(row, column_names, condition.left) or
                evaluate_condition(row, column_names, condition.right))
    else:
        raise ValueError(f"未知条件类型: {type(condition)}")


def _eval_expr(row: list, column_names: list[str], expr: Expr):
    """计算表达式的值：列引用 → 取对应值，字面值 → 直接返回"""
    if isinstance(expr, ColumnRef):
        try:
            idx = column_names.index(expr.name)
            return row[idx]
        except ValueError:
            raise ValueError(f"列 '{expr.name}' 不存在")
    elif isinstance(expr, Literal):
        return _parse_literal(expr.value)
    else:
        raise ValueError(f"未知表达式类型: {type(expr)}")


def _parse_literal(value: str):
    """把字符串字面值转成合适的 Python 类型"""
    # 尝试 int
    try:
        return int(value)
    except ValueError:
        pass
    # 尝试 float
    try:
        return float(value)
    except ValueError:
        pass
    # 字符串
    return value


def _eval_comparison(row: list, column_names: list[str],
                     comp: Comparison) -> bool:
    """计算单个比较操作"""
    left_val = _eval_expr(row, column_names, comp.left)
    right_val = _eval_expr(row, column_names, comp.right)

    # 空值处理
    if left_val is None or right_val is None:
        return False

    op = comp.op

    # 类型统一：如果一个是 int 另一个是 float，都转 float
    if isinstance(left_val, int) and isinstance(right_val, float):
        left_val = float(left_val)
    elif isinstance(left_val, float) and isinstance(right_val, int):
        right_val = float(right_val)

    if op == "=":
        return left_val == right_val
    elif op == "!=":
        return left_val != right_val
    elif op == "<":
        return left_val < right_val
    elif op == ">":
        return left_val > right_val
    elif op == "<=":
        return left_val <= right_val
    elif op == ">=":
        return left_val >= right_val
    else:
        raise ValueError(f"不支持的操作符: {op}")


def filter_table(table: Table, condition: Condition) -> Table:
    """对表执行 WHERE 过滤，返回新表。

    这就是关系代数中的 σ（选择）操作：
    σ_{condition}(Table) = { row ∈ Table | condition(row) 为 True }
    """
    column_names = table.column_names
    filtered_rows = []

    for row in table.rows:
        if evaluate_condition(row, column_names, condition):
            filtered_rows.append(row)

    return Table(schema=table.schema, rows=filtered_rows)
