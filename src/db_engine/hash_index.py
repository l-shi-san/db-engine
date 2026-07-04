"""
哈希索引 —— 用哈希表加速等值查询。

索引是数据库性能优化的核心手段。没有索引时，查询得"扫全表"（Full Table Scan）：
    逐行检查 → O(n)

有了哈希索引（Hash Index）：
    计算哈希值 → O(1) 查找 → 直接定位到行

就像书的目录 —— 没有目录就一页页翻，有目录直接翻到对应页码。

限制：
- 哈希索引只支持等值查询（=），不支持范围查询（>, <）
- 需要额外的存储空间
- 维护索引有成本（更新表时也要更新索引）
"""

from __future__ import annotations

from typing import Any

from .table import Table


class HashIndex:
    """哈希索引 —— 基于 Python dict 的简单实现。

    索引结构：
        { value: [row_index1, row_index2, ...] }

    一个值可能对应多行（非唯一列），所以用 list 存行号。
    """

    def __init__(self, table: Table, column_name: str):
        self.column_name = column_name
        self.column_index = table.get_column_index(column_name)
        self._index: dict[Any, list[int]] = {}

        self._build(table)

    def _build(self, table: Table):
        """遍历表，为指定列构建哈希索引。

        这就是"创建索引"的过程 —— 扫描全表，记录每个值出现的位置。
        """
        for row_idx, row in enumerate(table.rows):
            value = row[self.column_index]
            if value is None:
                continue
            if value not in self._index:
                self._index[value] = []
            self._index[value].append(row_idx)

    def lookup(self, value: Any) -> list[int]:
        """等值查找：根据值返回匹配的行号列表。

        这就是"走索引" —— O(1) 时间复杂度。
        """
        return self._index.get(value, [])

    def size(self) -> int:
        """返回索引中的键数量（不同值的个数）"""
        return len(self._index)

    def memory_estimate(self) -> str:
        """估算索引占用的内存（粗略）"""
        # Python dict 的 overhead 大约 72 bytes per entry
        num_entries = sum(len(rows) for rows in self._index.values())
        return f"~{num_entries * 72 / 1024:.0f} KB"


def index_lookup(table: Table, column_name: str, value: Any,
                 index: HashIndex | None = None) -> Table:
    """使用索引或全表扫描执行等值查询。

    这展示了"走索引 vs 全表扫描"的核心区别。
    """
    if index is not None:
        # 走索引：O(1) 找到行号，再根据行号取数据
        row_indices = index.lookup(value)
        return table.select_rows(row_indices)
    else:
        # 全表扫描：逐行检查 —— O(n)
        col_idx = table.get_column_index(column_name)
        matched_rows = [
            row for row in table.rows
            if row[col_idx] is not None and row[col_idx] == value
        ]
        return Table(schema=table.schema, rows=matched_rows)

