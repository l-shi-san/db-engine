"""
数据类型系统 —— 数据库引擎的基础。

数据库需要知道每列数据的"种类"（类型），才能正确地比较、运算。
就像你不能把"二十"和 20 直接比较一样 —— 一个是字符串，一个是整数。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union


# ──────────────────────────────────────────────
# 类型描述符（描述一列是什么类型）
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class IntType:
    """整数类型"""
    pass

    def __repr__(self):
        return "INTEGER"


@dataclass(frozen=True)
class FloatType:
    """浮点数类型"""
    pass

    def __repr__(self):
        return "FLOAT"


@dataclass(frozen=True)
class StringType:
    """字符串类型"""
    pass

    def __repr__(self):
        return "VARCHAR"


@dataclass(frozen=True)
class BoolType:
    """布尔类型"""
    pass

    def __repr__(self):
        return "BOOLEAN"


# 类型联合：一列的类型可以是这四种之一
ColumnType = Union[IntType, FloatType, StringType, BoolType]


# ──────────────────────────────────────────────
# 类型对应的 Python 原生类型
# ──────────────────────────────────────────────

TYPE_MAP: dict[type, ColumnType] = {
    int: IntType(),
    float: FloatType(),
    str: StringType(),
    bool: BoolType(),
}

PYTHON_TYPE_MAP: dict[type, type] = {
    IntType: int,
    FloatType: float,
    StringType: str,
    BoolType: bool,
}


def infer_type(values: list[str]) -> ColumnType:
    """从一组字符串值中推断列类型。

    规则：
    1. 如果全部可以转 int → INTEGER
    2. 否则如果全部可以转 float → FLOAT
    3. 否则如果只有 true/false → BOOLEAN
    4. 否则 → VARCHAR

    这是数据库的"类型推断" —— 就像 Excel 自动判断一列是数字还是文本。
    """
    non_empty = [v for v in values if v and v.strip()]

    if not non_empty:
        return StringType()

    # 尝试 int
    all_int = True
    for v in non_empty:
        try:
            int(v)
        except ValueError:
            all_int = False
            break
    if all_int:
        return IntType()

    # 尝试 float
    all_float = True
    for v in non_empty:
        try:
            float(v)
        except ValueError:
            all_float = False
            break
    if all_float:
        return FloatType()

    # 尝试 bool
    all_bool = True
    for v in non_empty:
        if v.strip().lower() not in ("true", "false", "1", "0", "yes", "no"):
            all_bool = False
            break
    if all_bool:
        return BoolType()

    return StringType()


def cast_value(value: str, col_type: ColumnType) -> Any:
    """将字符串转换为指定类型的 Python 值。

    这是数据库的"类型转换" —— 把读进来的字符串变成真正的整数/浮点数/布尔值。
    """
    if not value or not value.strip():
        return None
    stripped = value.strip()

    if isinstance(col_type, IntType):
        return int(stripped)
    elif isinstance(col_type, FloatType):
        return float(stripped)
    elif isinstance(col_type, BoolType):
        return stripped.lower() in ("true", "1", "yes")
    else:
        return stripped


def python_type_to_column_type(py_type: type) -> ColumnType:
    """将 Python 类型映射到列类型。"""
    return TYPE_MAP.get(py_type, StringType())
