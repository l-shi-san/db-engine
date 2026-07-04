"""
测试：SQL 解析器、过滤、聚合、排序、投影、引擎端到端
"""

from db_engine.parser import Parser, SelectColumn, AggFunction, Comparison, ColumnRef, Literal, OrderByItem
from db_engine.table import Column, Table
from db_engine.types import IntType, StringType, FloatType
from db_engine.filter import filter_table, evaluate_condition
from db_engine.aggregate import execute_aggregate, has_aggregate
from db_engine.sorter import sort_table
from db_engine.projection import project_table
from db_engine.engine import Engine, table_to_dicts


# ── 测试辅助：创建示例表 ──

def make_sample_table() -> Table:
    schema = [
        Column("Name", StringType()),
        Column("Age", IntType()),
        Column("City", StringType()),
        Column("Score", FloatType()),
    ]
    rows = [
        ["Tom", 20, "NYC", 85.0],
        ["Amy", 22, "LA", 92.0],
        ["Bob", 19, "NYC", 78.0],
        ["Alice", 21, "Chicago", 95.0],
        [None, 25, "LA", 88.0],  # NULL name
    ]
    return Table(schema=schema, rows=rows)


# ── 解析器测试 ──

class TestParser:
    def setup_method(self):
        self.parser = Parser()

    def test_simple_select(self):
        q = self.parser.parse("SELECT * FROM data.csv")
        assert len(q.select_items) == 1
        assert q.select_items[0].name == "*"
        assert q.table_name == "data.csv"

    def test_select_columns(self):
        q = self.parser.parse("SELECT Name, Age FROM data.csv")
        assert len(q.select_items) == 2
        assert q.select_items[0].name == "Name"
        assert q.select_items[1].name == "Age"

    def test_where_comparison(self):
        q = self.parser.parse("SELECT * FROM data WHERE Age > 18")
        assert q.where is not None
        from db_engine.parser import Comparison
        assert isinstance(q.where, Comparison)
        assert q.where.op == ">"

    def test_where_and(self):
        q = self.parser.parse("SELECT * FROM data WHERE Age > 18 AND City = 'NYC'")
        from db_engine.parser import LogicalAnd
        assert isinstance(q.where, LogicalAnd)

    def test_where_or(self):
        q = self.parser.parse("SELECT * FROM data WHERE Age > 20 OR Score >= 90")
        from db_engine.parser import LogicalOr
        assert isinstance(q.where, LogicalOr)

    def test_order_by(self):
        q = self.parser.parse("SELECT * FROM data ORDER BY Age DESC")
        assert len(q.order_by) == 1
        assert q.order_by[0].column == "Age"
        assert q.order_by[0].ascending == False

    def test_order_by_multi(self):
        q = self.parser.parse("SELECT * FROM data ORDER BY Age DESC, Name ASC")
        assert len(q.order_by) == 2

    def test_aggregate(self):
        q = self.parser.parse("SELECT COUNT(*), AVG(Age) FROM data")
        assert isinstance(q.select_items[0], AggFunction)
        assert q.select_items[0].name == "COUNT"
        assert isinstance(q.select_items[1], AggFunction)
        assert q.select_items[1].name == "AVG"

    def test_select_star_from_csv(self):
        q = self.parser.parse("SELECT * FROM test_data.csv")
        assert q.select_items[0].name == "*"


# ── 过滤测试 ──

class TestFilter:
    def setup_method(self):
        self.table = make_sample_table()

    def test_filter_eq(self):
        from db_engine.parser import Comparison, ColumnRef, Literal
        cond = Comparison(ColumnRef("Age"), "=", Literal("22"))
        result = filter_table(self.table, cond)
        assert len(result.rows) == 1
        assert result.rows[0][1] == 22

    def test_filter_gt(self):
        from db_engine.parser import Comparison, ColumnRef, Literal
        cond = Comparison(ColumnRef("Age"), ">", Literal("21"))
        result = filter_table(self.table, cond)
        assert len(result.rows) == 2  # Amy(22), NULL(25)

    def test_filter_and(self):
        from db_engine.parser import Comparison, ColumnRef, Literal, LogicalAnd
        c1 = Comparison(ColumnRef("Age"), ">=", Literal("21"))
        c2 = Comparison(ColumnRef("Score"), ">", Literal("90"))
        cond = LogicalAnd(c1, c2)
        result = filter_table(self.table, cond)
        assert len(result.rows) == 2  # Amy(Age=22, Score=92) + Alice(Age=21, Score=95)
        assert result.rows[0][0] == "Amy"
        assert result.rows[1][0] == "Alice"

    def test_filter_not_equal(self):
        from db_engine.parser import Comparison, ColumnRef, Literal
        cond = Comparison(ColumnRef("City"), "!=", Literal("NYC"))
        result = filter_table(self.table, cond)
        # LA(None/Amy/Bob-no), Chicago(Alice), LA(None)
        for row in result.rows:
            assert row[2] != "NYC"


# ── 聚合测试 ──

class TestAggregate:
    def setup_method(self):
        self.table = make_sample_table()

    def test_count(self):
        from db_engine.parser import AggFunction
        val = execute_aggregate(self.table, AggFunction("COUNT", "*"))
        assert val == 5

    def test_avg(self):
        from db_engine.parser import AggFunction
        val = execute_aggregate(self.table, AggFunction("AVG", "Age"))
        # (20+22+19+21+25)/5 = 21.4
        assert val == 21.4

    def test_sum(self):
        from db_engine.parser import AggFunction
        val = execute_aggregate(self.table, AggFunction("SUM", "Score"))
        # 85+92+78+95+88 = 438
        assert val == 438.0

    def test_max_min(self):
        from db_engine.parser import AggFunction
        max_val = execute_aggregate(self.table, AggFunction("MAX", "Age"))
        min_val = execute_aggregate(self.table, AggFunction("MIN", "Age"))
        assert max_val == 25
        assert min_val == 19

    def test_has_aggregate_true(self):
        from db_engine.parser import AggFunction
        assert has_aggregate([AggFunction("COUNT", "*")]) == True

    def test_has_aggregate_false(self):
        assert has_aggregate([]) == False


# ── 排序测试 ──

class TestSorter:
    def setup_method(self):
        self.table = make_sample_table()

    def test_sort_asc(self):
        result = sort_table(self.table, [OrderByItem("Age", ascending=True)])
        ages = [row[1] for row in result.rows]
        assert ages == [19, 20, 21, 22, 25]

    def test_sort_desc(self):
        result = sort_table(self.table, [OrderByItem("Age", ascending=False)])
        ages = [row[1] for row in result.rows]
        assert ages == [25, 22, 21, 20, 19]


# ── 端到端引擎测试 ──

class TestEngine:
    def setup_method(self):
        self.engine = Engine()

    def test_select_star(self):
        # 直接用我们创建的小测试文件
        import tempfile, csv, os
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        tmp.write("Name,Age\nTom,20\nAmy,22\n")
        tmp.close()
        try:
            result = self.engine.execute(f"SELECT * FROM {tmp.name}")
            assert len(result) == 2
            assert result[0]["Name"] == "Tom"
        finally:
            os.unlink(tmp.name)

    def test_where(self):
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        tmp.write("Name,Age\nTom,20\nAmy,22\nBob,19\n")
        tmp.close()
        try:
            result = self.engine.execute(f"SELECT Name, Age FROM {tmp.name} WHERE Age >= 20")
            assert len(result) == 2
            assert result[0]["Name"] in ("Tom", "Amy")
        finally:
            os.unlink(tmp.name)

    def test_aggregate(self):
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        tmp.write("Name,Age\nTom,20\nAmy,22\nBob,19\n")
        tmp.close()
        try:
            result = self.engine.execute(f"SELECT COUNT(*), AVG(Age) FROM {tmp.name}")
            assert len(result) == 1
            assert result[0]["COUNT(*)"] == 3
            # (20+22+19)/3 ≈ 20.33
        finally:
            os.unlink(tmp.name)
