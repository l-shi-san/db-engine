"""
投影模块 —— SELECT 列选择。

投影（Projection）就是选择"要哪些列"。
     SELECT Name, Age FROM students
     → 结果表中只保留 Name 和 Age 两列

这就是关系代数中的 π（投影）操作：
π_{col1, col2}(Table) = 只保留 col1 和 col2 两列
"""

from __future__ import annotations

from .table import Table
from .parser import SelectColumn


def project_table(table: Table, columns: list[SelectColumn]) -> Table:
    """执行投影操作：只保留 SELECT 指定的列。"""
    if not columns:
        return table

    # 检查是否包含 *
    if any(col.name == "*" for col in columns):
        return table

    # 找到要保留列的索引
    col_indices = []
    new_schema_items = []
    for sel_col in columns:
        name = sel_col.name
        if sel_col.alias:
            name = sel_col.alias
        try:
            idx = table.get_column_index(sel_col.name)
            col_indices.append(idx)
            new_schema_items.append(table.schema[idx])
            # 如果有别名，更新列名
            if sel_col.alias:
                from .types import StringType
                new_schema_items[-1] = type(table.schema[idx])(
                    name=sel_col.alias,
                    col_type=table.schema[idx].col_type
                )
        except ValueError:
            raise ValueError(f"列 '{sel_col.name}' 不存在")

    # 手动构建新表（带上别名）
    new_rows = []
    for row in table.rows:
        new_rows.append([row[i] for i in col_indices])

    from .table import Table
    return Table(schema=new_schema_items, rows=new_rows)
