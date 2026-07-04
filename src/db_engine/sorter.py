"""
排序模块 —— ORDER BY 实现。

排序是数据库中最常用的操作之一。
数据库需要能够按一列或多列对结果排序，支持升序（ASC）和降序（DESC）。
"""

from __future__ import annotations

from .table import Table
from .parser import OrderByItem


def sort_table(table: Table, order_by: list[OrderByItem]) -> Table:
    """对表进行排序。

    支持多列排序：先按第一列排，相同再按第二列排。
    这就像 Excel 的"自定义排序"功能。
    """
    if not order_by:
        return table

    def sort_key(row):
        """生成排序键。

        对于多列排序，返回一个元组。
        元组比较会自动按顺序比较每个元素。
        NULL 统一放在最后（无论 ASC/DESC）。
        """
        keys = []
        for item in order_by:
            try:
                idx = table.get_column_index(item.column)
            except ValueError:
                raise ValueError(f"排序列 '{item.column}' 不存在")

            val = row[idx]

            if val is None:
                # NULL 永远排最后（优先级 1 大于 0）
                keys.append((1, 0, 0))
            else:
                # 非 NULL：优先级 0
                if isinstance(val, (int, float)):
                    # 数值：降序取负
                    keys.append((0, 0, -val if not item.ascending else val))
                else:
                    # 字符串：降序时用反向字符映射
                    str_val = str(val)
                    if not item.ascending:
                        # 对每个字符取补码实现反向排序
                        reversed_str = ''.join(
                            chr(0x10FFFF - ord(c)) for c in str_val
                        )
                        keys.append((0, 1, reversed_str))
                    else:
                        keys.append((0, 1, str_val))

        return tuple(keys)

    new_rows = sorted(table.rows, key=sort_key)
    return Table(schema=table.schema, rows=new_rows)
