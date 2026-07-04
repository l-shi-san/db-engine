# 轻量级数据库引擎

**题目二 · 子模块 A+B+C** — 数据库原理课程项目

从零实现的轻量级数据库查询引擎，以 CSV 文件作为外部存储，支持单表 SQL 查询、哈希索引、列式存储和 NL2SQL 自然语言查询。

---

## 项目结构

```
├── src/db_engine/          # 核心源码（15 个模块）
│   ├── cli.py              # CLI 交互界面
│   ├── engine.py           # 查询引擎
│   ├── parser.py           # SQL 解析器
│   ├── filter.py           # 条件过滤
│   ├── aggregate.py        # 聚合函数
│   ├── sorter.py           # 排序
│   ├── projection.py       # 投影
│   ├── hash_index.py       # 哈希索引
│   ├── columnar_store.py   # 列式存储（子模块 B）
│   ├── nl2sql.py           # NL2SQL（子模块 C）
│   ├── csv_loader.py       # CSV 加载器
│   ├── table.py            # 行式存储模型
│   └── types.py            # 数据类型系统
├── tests/                  # 测试（28 个用例）
├── experiments/            # 性能实验脚本
├── data/                   # 测试数据
│   └── large_test.csv      # 10 万行测试数据
├── learn-diary.md          # 学习总结
└── pyproject.toml          # 项目配置
```

---

## 环境要求

- Python >= 3.12
- uv（包管理器）

## 快速开始

```bash
# 1. 进入项目目录
cd D:\数据库期末作业

# 2. 激活虚拟环境
.venv\Scripts\activate

# 3. 运行 CLI 交互界面
python -m db_engine.cli

# 4. 或在命令行直接查询
python -m db_engine.cli "SELECT * FROM test_data.csv"
```

## 支持的 SQL 语法

| 功能 | 示例 |
|------|------|
| 全部查询 | `SELECT * FROM test_data.csv` |
| 列投影 | `SELECT Name, Age FROM test_data.csv` |
| 条件过滤 | `SELECT * FROM test_data.csv WHERE Age > 20` |
| AND/OR 组合 | `SELECT * FROM test_data.csv WHERE Age > 20 AND City = 'NYC'` |
| 不等查询 | `SELECT * FROM test_data.csv WHERE City != 'NYC'` |
| 排序 | `SELECT * FROM test_data.csv ORDER BY Score DESC` |
| 多列排序 | `SELECT * FROM test_data.csv ORDER BY Age ASC, Score DESC` |
| 聚合 | `SELECT COUNT(*), AVG(Age), MAX(Score) FROM test_data.csv` |
| 退出 | `QUIT` |

## 运行测试

```bash
# 全部 28 个测试
python -m pytest tests/ -v

# 单独测试某个模块
python -m pytest tests/test_core.py -v
```

## 性能实验

```bash
# 哈希索引对比实验（子模块 A）
python experiments/benchmark_index.py data/large_test.csv 20

# 列式 vs 行式存储对比实验（子模块 B）
python experiments/benchmark_columnar_vs_row.py data/large_test.csv
```

## NL2SQL 自然语言查询（子模块 C）

```bash
python -m db_engine.nl2sql
```

支持 12 个测试用例，覆盖全表查询、条件过滤、排序、聚合等场景。

## 实验结论

| 实验 | 结果 |
|------|------|
| 哈希索引（10 万行） | 有索引 0.0013 ms / 无索引 2.08 ms / **加速比 1646×** |
| 列式 vs 行式（聚合） | 列存快 **1.4×** |
| 列式 vs 行式（全行读取） | 行存快 **158,241×** |
| 功能测试 | **28/28 通过** |

## 技术限制

- 纯 Python 实现，未使用 Pandas、SQLite、DuckDB 等现有数据库引擎
- 仅支持单表查询，不支持 JOIN、GROUP BY
- 哈希索引仅支持等值查询（=）

## 课程信息

- **课程**：数据库原理
- **题目**：题目二 — 轻量级数据库引擎（子模块 A+B+C）
- **专业**：计算机科学与技术
