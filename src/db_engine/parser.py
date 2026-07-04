"""
SQL 查询解析器 —— 把用户输入的文本 SQL 解析成结构化指令。

SQL 解析是数据库引擎的"入口"。用户输入：
    SELECT Name, Age FROM students WHERE Age > 18 ORDER BY Age DESC

解析器需要把这个字符串拆解成：
    - 要查的列: ["Name", "Age"]
    - 从哪查: "students"
    - 过滤条件: Age > 18
    - 排序: Age 降序

这就是数据库的"SQL 解析"（Parsing）阶段。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# 表达式（条件中的值或列引用）
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class ColumnRef:
    """引用一个列，如 Age"""
    name: str


@dataclass(frozen=True)
class Literal:
    """字面值，如 18, 'hello'"""
    value: str


Expr = ColumnRef | Literal


# ──────────────────────────────────────────────
# 操作符
# ──────────────────────────────────────────────

COMPARISON_OPS = {"=", "!=", "<", ">", "<=", ">="}
LOGICAL_OPS = {"AND", "OR"}


# ──────────────────────────────────────────────
# 条件节点（过滤条件）
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class Comparison:
    """比较表达式，如 Age > 18"""
    left: Expr
    op: str       # =, !=, <, >, <=, >=
    right: Expr


@dataclass(frozen=True)
class LogicalAnd:
    """AND 组合"""
    left: Condition
    right: Condition


@dataclass(frozen=True)
class LogicalOr:
    """OR 组合"""
    left: Condition
    right: Condition


Condition = Comparison | LogicalAnd | LogicalOr


# ──────────────────────────────────────────────
# 排序
# ──────────────────────────────────────────────

@dataclass
class OrderByItem:
    """ORDER BY 中的一项"""
    column: str
    ascending: bool = True


# ──────────────────────────────────────────────
# 聚合类型
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class AggFunction:
    """聚合函数调用，如 COUNT(*), SUM(Age)"""
    name: str    # COUNT, SUM, AVG, MAX, MIN
    column: str  # 列名 或 "*"


# ──────────────────────────────────────────────
# SELECT 项
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class SelectColumn:
    """SELECT 中的一个列"""
    name: str
    alias: Optional[str] = None


SelectItem = SelectColumn | AggFunction


# ──────────────────────────────────────────────
# 完整查询
# ──────────────────────────────────────────────

@dataclass
class Query:
    """解析后的完整查询"""
    select_items: list[SelectItem]        # SELECT 后面的内容
    table_name: str                       # FROM 后面的表名（CSV 文件路径）
    where: Optional[Condition] = None     # WHERE 条件
    order_by: list[OrderByItem] = field(default_factory=list)  # ORDER BY


# ──────────────────────────────────────────────
# 解析器
# ──────────────────────────────────────────────

class ParserError(Exception):
    """SQL 解析错误"""
    pass


class Parser:
    """SQL 查询解析器.

    支持语法：
        SELECT col1, col2 FROM file
        SELECT * FROM file
        SELECT col1, col2 FROM file WHERE col = val AND col > val
        SELECT col1, col2 FROM file ORDER BY col1 ASC, col2 DESC
        SELECT COUNT(*), SUM(col) FROM file WHERE ...
        SELECT AVG(col) FROM file
    """

    def parse(self, sql: str) -> Query:
        """解析一条 SQL 查询语句。"""
        sql = sql.strip()

        if not sql.upper().startswith("SELECT"):
            raise ParserError("查询必须以 SELECT 开头")

        # 去除末尾的分号
        if sql.endswith(";"):
            sql = sql[:-1].strip()

        # 拆分成子句
        # 按关键字分割：SELECT ... FROM ... WHERE ... ORDER BY ...
        clause_pattern = re.compile(
            r'\b(SELECT|FROM|WHERE|ORDER\s+BY)\b',
            re.IGNORECASE
        )
        parts = clause_pattern.split(sql)

        # 清理空白并配对
        clauses: dict[str, str] = {}
        current_keyword = None
        for part in parts:
            part = part.strip()
            if not part:
                continue
            upper = part.upper()
            if upper in ("SELECT", "FROM", "WHERE", "ORDER BY"):
                # 可能 "ORDER" 和 "BY" 被分开了
                if upper == "ORDER":
                    continue  # 忽略 ORDER，等 BY
                if upper == "BY" and current_keyword == "ORDER":
                    # 合并 ORDER BY
                    continue
                current_keyword = upper
                # ORDER BY 已经合并了
            elif current_keyword:
                if current_keyword in clauses:
                    clauses[current_keyword] += " " + part
                else:
                    clauses[current_keyword] = part

        # 重新处理 ORDER BY
        # 如果 clauses 有 ORDER，它其实是 "ORDER BY xxx"
        # 在 split 时 ORDER 和 BY 可能被分开
        # 更稳健的方法：用正则完整匹配
        return self._parse_clauses(sql)

    def _parse_clauses(self, sql: str) -> Query:
        """更稳健的解析：逐个子句提取。"""
        query = Query(select_items=[], table_name="")

        # 提取 SELECT ... FROM 之间的内容
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM\b', sql, re.IGNORECASE)
        if not select_match:
            raise ParserError("缺少 FROM 子句")
        select_part = select_match.group(1).strip()
        query.select_items = self._parse_select(select_part)

        # 提取 FROM ... WHERE/ORDER BY/END 之间的内容
        from_match = re.search(r'FROM\s+(\S+)', sql, re.IGNORECASE)
        if not from_match:
            raise ParserError("缺少表名")
        query.table_name = from_match.group(1).strip()

        # 提取 WHERE ... ORDER BY/END 之间的内容
        where_match = re.search(
            r'WHERE\s+(.+?)(?:\s+ORDER\s+BY\s+|$)', sql, re.IGNORECASE
        )
        if where_match:
            where_part = where_match.group(1).strip()
            query.where = self._parse_condition(where_part)

        # 提取 ORDER BY ... 之后的内容
        order_match = re.search(r'ORDER\s+BY\s+(.+?)$', sql, re.IGNORECASE)
        if order_match:
            order_part = order_match.group(1).strip()
            query.order_by = self._parse_order_by(order_part)

        return query

    def _parse_select(self, part: str) -> list[SelectItem]:
        """解析 SELECT 后面的内容。"""
        items = []
        for item in part.split(","):
            item = item.strip()
            if not item:
                continue

            # 检查是否是聚合函数
            agg_match = re.match(
                r'(COUNT|SUM|AVG|MAX|MIN)\s*\(\s*(.+?)\s*\)',
                item,
                re.IGNORECASE
            )
            if agg_match:
                func_name = agg_match.group(1).upper()
                col_name = agg_match.group(2).strip()
                items.append(AggFunction(name=func_name, column=col_name))
                continue

            # 普通列或 *
            if item == "*":
                items.append(SelectColumn(name="*"))
            else:
                # 检查是否有别名 AS
                as_match = re.match(r'(.+?)\s+AS\s+(.+?)$', item, re.IGNORECASE)
                if as_match:
                    items.append(SelectColumn(
                        name=as_match.group(1).strip(),
                        alias=as_match.group(2).strip()
                    ))
                else:
                    items.append(SelectColumn(name=item))

        return items

    def _parse_condition(self, part: str) -> Condition:
        """解析 WHERE 后的条件表达式。

        处理优先级：AND 优先于 OR （简化起见，不支持括号嵌套）
        """
        # 先按 OR 分割
        or_parts = self._split_by_keyword(part, "OR")
        if len(or_parts) > 1:
            conditions = [self._parse_and_condition(p.strip()) for p in or_parts]
            result = conditions[0]
            for cond in conditions[1:]:
                result = LogicalOr(left=result, right=cond)
            return result

        # 再按 AND 分割
        return self._parse_and_condition(part)

    def _parse_and_condition(self, part: str) -> Condition:
        """解析 AND 连接的条件。"""
        and_parts = self._split_by_keyword(part, "AND")
        if len(and_parts) > 1:
            conditions = [self._parse_comparison(p.strip()) for p in and_parts]
            result = conditions[0]
            for cond in conditions[1:]:
                result = LogicalAnd(left=result, right=cond)
            return result

        return self._parse_comparison(part)

    def _split_by_keyword(self, text: str, keyword: str) -> list[str]:
        """按关键字分割，但忽略字符串内的关键字。"""
        parts = []
        current = []
        i = 0
        text_upper = text.upper()
        kw_upper = keyword.upper()
        kw_len = len(keyword)

        while i < len(text):
            # 检查是否在字符串中
            if text[i] in ("'", '"'):
                quote = text[i]
                current.append(text[i])
                i += 1
                while i < len(text) and text[i] != quote:
                    current.append(text[i])
                    i += 1
                if i < len(text):
                    current.append(text[i])
                    i += 1
                continue

            # 检查关键字
            if (text_upper[i:i+kw_len] == kw_upper and
                    (i + kw_len >= len(text) or text[i+kw_len] in (' ', '\t', '(')) and
                    (i == 0 or text[i-1] in (' ', '\t', ')'))):
                parts.append("".join(current).strip())
                current = []
                i += kw_len
                continue

            current.append(text[i])
            i += 1

        parts.append("".join(current).strip())
        return [p for p in parts if p]

    def _parse_comparison(self, part: str) -> Comparison:
        """解析单个比较表达式，如 Age > 18"""
        # 从最长的操作符开始匹配
        for op in sorted(COMPARISON_OPS, key=len, reverse=True):
            # 匹配操作符，但不在字符串内
            parts = self._split_by_op(part, op)
            if len(parts) == 2:
                left = self._parse_expr(parts[0].strip())
                right = self._parse_expr(parts[1].strip())
                return Comparison(left=left, op=op, right=right)

        raise ParserError(f"无法解析条件表达式: {part}")

    def _split_by_op(self, text: str, op: str) -> list[str]:
        """按操作符分割表达式。"""
        parts = []
        current = []
        i = 0
        op_len = len(op)

        while i < len(text):
            if text[i] in ("'", '"'):
                quote = text[i]
                current.append(text[i])
                i += 1
                while i < len(text) and text[i] != quote:
                    current.append(text[i])
                    i += 1
                if i < len(text):
                    current.append(text[i])
                    i += 1
                continue

            if text[i:i+op_len] == op:
                # 确保是独立操作符（不是另一个符号的一部分）
                parts.append("".join(current).strip())
                current = []
                i += op_len
                continue

            current.append(text[i])
            i += 1

        parts.append("".join(current).strip())
        return parts

    def _parse_expr(self, text: str) -> Expr:
        """解析一个表达式：列名或字面值。"""
        text = text.strip()

        # 字符串字面值
        if (text.startswith("'") and text.endswith("'")) or \
           (text.startswith('"') and text.endswith('"')):
            return Literal(value=text[1:-1])

        # 数字字面值
        try:
            float(text)
            return Literal(value=text)
        except ValueError:
            pass

        # 否则视为列名
        return ColumnRef(name=text)

    def _parse_order_by(self, part: str) -> list[OrderByItem]:
        """解析 ORDER BY 后面的内容。"""
        items = []
        for item in part.split(","):
            item = item.strip()
            if not item:
                continue

            # 检查 DESC/ASC
            upper = item.upper()
            if upper.endswith(" DESC"):
                col = item[:-5].strip()
                items.append(OrderByItem(column=col, ascending=False))
            elif upper.endswith(" ASC"):
                col = item[:-4].strip()
                items.append(OrderByItem(column=col, ascending=True))
            else:
                items.append(OrderByItem(column=item, ascending=True))

        return items
