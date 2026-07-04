"""
行式存储模型 —— 以"行"为单位存储数据。

行式存储（Row-Oriented Storage）是最直观的存储方式：
把每一行数据连续地存在一起，就像 Excel 表格一样。

内存结构：
    columns: ["Name", "Age", "City"]
    rows:    [["Tom",  20,   "NYC"],
              ["Amy",  22,   "LA"]]

在数据库中，这叫"行存"（Row Store）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import ColumnType, infer_type, cast_value


@dataclass
class Column:
    """描述表中的一列"""
    name: str
    col_type: ColumnType

    def __repr__(self):
        return f"{self.name}: {self.col_type}"


@dataclass
class Table:
    """行式存储的表。

    这就是数据库中的"关系"（Relation）—— 一个二维表格。
    - schema: 列的定义（列名 + 类型）
    - rows: 数据行，每行是一个列表，值与 schema 中的列一一对应
    """
    schema: list[Column]                         # 列定义
    rows: list[list[Any]] = field(default_factory=list)  # 数据行

    @property
    def column_names(self) -> list[str]:
        return [col.name for col in self.schema]

    @property
    def num_rows(self) -> int:
        return len(self.rows)

    @property
    def num_columns(self) -> int:
        return len(self.schema)

    def get_column_index(self, name: str) -> int:
        """根据列名找到列索引"""
        for i, col in enumerate(self.schema):
            if col.name == name:
                return i
        raise ValueError(f"列 '{name}' 不存在")

    def get_column(self, name: str) -> list[Any]:
        """获取某一列的所有值（用于聚合操作）"""
        idx = self.get_column_index(name)
        return [row[idx] for row in self.rows]

    def select_rows(self, indices: list[int]) -> Table:
        """根据行号列表选择子集，返回新表"""
        new_rows = [self.rows[i] for i in indices]
        return Table(schema=self.schema, rows=new_rows)

    def select_columns(self, col_indices: list[int]) -> Table:
        """根据列号列表选择子集（投影）"""
        new_schema = [self.schema[i] for i in col_indices]
        new_rows = [[row[i] for i in col_indices] for row in self.rows]
        return Table(schema=new_schema, rows=new_rows)

    def __repr__(self):
        if not self.rows:
            return f"Table(schema={self.schema}, rows=0)"
        return f"Table(schema={self.schema}, rows={self.num_rows})"

    def display(self, max_rows: int = 20) -> str:
        """格式化输出表格内容"""
        lines = []
        # 表头
        header = " | ".join(f"{col.name}({col.col_type})" for col in self.schema)
        sep = "-" * len(header)
        lines.append(header)
        lines.append(sep)

        # 数据行
        for i, row in enumerate(self.rows):
            if i >= max_rows:
                lines.append(f"... 还有 {self.num_rows - max_rows} 行")
                break
            lines.append(" | ".join(str(v) if v is not None else "NULL" for v in row))

        return "\n".join(lines)
