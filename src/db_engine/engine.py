"""
查询引擎 —— 把解析、过滤、聚合、排序、投影串成一条流水线。

一条 SQL 查询的执行流程：
    SELECT Name, AVG(Age) FROM students WHERE Age > 18 ORDER BY Name

    1. 解析 SQL → Query 对象
    2. 加载 CSV → Table（行式存储）
    3. 过滤 WHERE → 筛选后的 Table
    4. 聚合 GROUP（如果有）→ 聚合结果
    5. 排序 ORDER BY → 排序后的 Table
    6. 投影 SELECT → 只保留指定列

这就是数据库的"查询执行计划"（Query Execution Plan）。
专业的数据库还会做"查询优化"—— 调整步骤顺序以提升性能。
"""

from __future__ import annotations

from pathlib import Path

from .table import Table
from .csv_loader import load_csv
from .parser import Parser, SelectColumn, AggFunction
from .filter import filter_table
from .aggregate import execute_aggregate, has_aggregate
from .sorter import sort_table
from .projection import project_table


class Engine:
    """数据库查询引擎"""

    def __init__(self):
        self.parser = Parser()
        self._loaded: dict[str, Table] = {}  # 缓存已加载的表

    def execute(self, sql: str) -> list[dict] | Table:
        """执行一条 SQL 查询，返回结果"""
        query = self.parser.parse(sql)

        # 加载表（CSV 文件）
        table = self._load_table(query.table_name)

        # 执行 WHERE 过滤（如果有）
        if query.where is not None:
            table = filter_table(table, query.where)

        # 判断是否有聚合函数
        if has_aggregate(query.select_items):
            return self._execute_aggregate_query(table, query.select_items)

        # ORDER BY 排序
        if query.order_by:
            table = sort_table(table, query.order_by)

        # 投影 SELECT 列
        select_cols = [item for item in query.select_items
                       if isinstance(item, SelectColumn)]
        if select_cols:
            table = project_table(table, select_cols)

        # 转成字典列表返回
        return table_to_dicts(table)

    def _load_table(self, name: str) -> Table:
        """加载表（带缓存）"""
        if name in self._loaded:
            return self._loaded[name]

        # 以 engine.py 所在目录为参考点，定位项目根目录
        module_dir = Path(__file__).resolve().parent  # src/db_engine/
        project_root = module_dir.parent.parent       # 项目根目录

        # 尝试的路径列表
        search_paths = [
            Path(name),
            project_root / name,
            project_root / "data" / f"{name}.csv",
        ]
        if not name.endswith('.csv'):
            search_paths.append(project_root / f"{name}.csv")

        seen = set()
        for sp in search_paths:
            resolved = sp.resolve()
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            if resolved.exists():
                table = load_csv(resolved)
                self._loaded[name] = table
                return table

        raise FileNotFoundError(
            f"找不到文件: {name}（已尝试项目根目录: {project_root}）"
        )

    def _execute_aggregate_query(self, table: Table,
                                 select_items: list) -> list[dict]:
        """执行聚合查询（SELECT COUNT(*), SUM(Age) FROM ...）"""
        result = {}
        has_agg = False
        has_col = False
        for item in select_items:
            if isinstance(item, AggFunction):
                has_agg = True
                val = execute_aggregate(table, item)
                col_name = f"{item.name}({item.column})"
                result[col_name] = val
            elif isinstance(item, SelectColumn):
                has_col = True
        if has_agg and has_col:
            raise ValueError(
                "不支持聚合函数与普通列的混合查询（需要 GROUP BY 子句，"
                "本引擎暂未实现）"
            )
        return [result]


def table_to_dicts(table: Table) -> list[dict]:
    """将 Table 转换为字典列表（方便输出）"""
    col_names = table.column_names
    return [dict(zip(col_names, row)) for row in table.rows]
