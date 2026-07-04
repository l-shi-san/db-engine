"""
测试：数据类型系统
"""

from db_engine.types import (
    IntType, FloatType, StringType, BoolType,
    infer_type, cast_value
)


def test_infer_type():
    """测试类型推断"""
    assert isinstance(infer_type(["1", "2", "3"]), IntType)
    assert isinstance(infer_type(["1.5", "2.3", "3.0"]), FloatType)
    assert isinstance(infer_type(["hello", "world"]), StringType)
    assert isinstance(infer_type(["true", "false"]), BoolType)
    assert isinstance(infer_type(["yes", "no"]), BoolType)
    # "1"/"0" 优先推断为整数（数字优先于布尔）
    assert isinstance(infer_type(["1", "0"]), IntType)
    assert isinstance(infer_type(["1", "hello"]), StringType)


def test_cast_value():
    """测试类型转换"""
    assert cast_value("42", IntType()) == 42
    assert cast_value("3.14", FloatType()) == 3.14
    assert cast_value("hello", StringType()) == "hello"
    assert cast_value("true", BoolType()) is True
    assert cast_value("false", BoolType()) is False
    assert cast_value("1", BoolType()) is True
    assert cast_value("0", BoolType()) is False
    assert cast_value("", IntType()) is None
    assert cast_value("", StringType()) is None
