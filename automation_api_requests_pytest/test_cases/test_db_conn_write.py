# test_cases/test_db_conn_write.py
# 【任务 #3.8：数据库 —— 连接复用 + 写操作 + 日志】
#
# 本文件不改任何已有文件，专门验证 common/db.py 从 v1 升级到 v2 后新增的三件事：
#   ① 连接复用 —— 不再"每次调用都新建连接"（坑一）
#   ② 写能力   —— execute / executemany / transaction（坑二）
#   ③ SQL 日志 —— 跑测试时能看到每条 SQL 的参数、行数、耗时
#
# 纪律：造数据只用 tmp_ 前缀的临时表，用完必须拆掉（见 tmp_table 夹具）。

import pymysql
import pytest

import common.db as db
from common.db import execute, executemany, query, transaction

TABLE = "tmp_db_learn"   # tmp_ 前缀 = 一眼看出是测试垃圾，不是业务数据


@pytest.fixture
def tmp_table():
    """准备一张临时表，测试跑完（哪怕跑挂了）都拆掉。"""
    execute(f"drop table if exists {TABLE}")
    execute(f"create table {TABLE} (id int primary key auto_increment, name varchar(50) not null)")
    yield TABLE
    execute(f"drop table if exists {TABLE}")


# ==================== ① 连接复用 ====================
def test_connection_is_reused():
    """连续两次取连接，拿到的应该是**同一个对象**（is 比的是对象身份，不是值）。"""
    assert db.get_conn() is db.get_conn(), "应当是同一条连接，不该每次新建"


def test_five_queries_share_one_connection(monkeypatch):
    """硬证据：数一数 pymysql.connect 到底被调用了几次。

    monkeypatch 是 pytest 的"临时替换"工具：测试结束会自动还原，
    不会污染别的用例（这类"改环境"的东西绝不能用手写赋值）。
    """
    calls = {"n": 0}
    real_connect = pymysql.connect

    def counting_connect(*args, **kwargs):
        calls["n"] += 1
        return real_connect(*args, **kwargs)

    db.close_conn()                                        # 先清空，保证从 0 开始数
    monkeypatch.setattr(pymysql, "connect", counting_connect)

    for _ in range(5):
        query("select 1 as x", one=True)

    assert calls["n"] == 1, f"5 次查询只该建 1 条连接，实际建了 {calls['n']} 条"


# ==================== 读：one=True ====================
def test_query_one_returns_single_dict(tmp_table):
    """one=True → 只返回一行（dict）；查不到返回 None，而不是空列表。"""
    execute(f"insert into {tmp_table}(name) values (%s)", ("唯一一行",))

    row = query(f"select name from {tmp_table}", one=True)
    assert isinstance(row, dict)
    assert row["name"] == "唯一一行"

    assert query(f"select name from {tmp_table} where id = -1", one=True) is None


# ==================== ② 写：execute ====================
def test_execute_then_query_roundtrip(tmp_table):
    """写进去，再读出来 —— 顺便在日志里看到 WRITE 和 SELECT 两行。"""
    affected = execute(f"insert into {tmp_table}(name) values (%s)", ("燕麦粥",))
    assert affected == 1, "插入一行，受影响行数应为 1"

    rows = query(f"select name from {tmp_table} order by id")
    assert [r["name"] for r in rows] == ["燕麦粥"]


# ==================== ② 写：executemany 批量 ====================
def test_executemany_bulk_insert(tmp_table):
    """批量写：一条 SQL × 3 组参数，只发一次请求。"""
    affected = executemany(
        f"insert into {tmp_table}(name) values (%s)",
        [("早餐",), ("午餐",), ("晚餐",)],
    )
    assert affected == 3

    total = query(f"select count(*) as c from {tmp_table}", one=True)
    assert total["c"] == 3


# ==================== ② 写：transaction 事务 ====================
def test_transaction_rollback_leaves_nothing(tmp_table):
    """事务的价值："造数据 → 验证 → 撤销"里那个最容易忘的"撤销"，交给它。"""
    with pytest.raises(RuntimeError):
        with transaction() as cur:
            cur.execute(f"insert into {tmp_table}(name) values (%s)", ("本该被回滚的数据",))
            assert cur.rowcount == 1                       # 事务内自己看得见这行

            raise RuntimeError("故意抛错：整个事务应当回滚")   # 让它炸，看数据会不会留下

    rows = query(f"select name from {tmp_table} where name = %s", ("本该被回滚的数据",))
    assert rows == [], "回滚之后，那行数据必须不存在"


def test_transaction_commit_when_no_error(tmp_table):
    """反过来：不抛异常就正常提交 —— 证明上面那条断言不是"因为压根写不进去"。"""
    with transaction() as cur:
        cur.execute(f"insert into {tmp_table}(name) values (%s)", ("正常提交的数据",))

    assert query(f"select count(*) as c from {tmp_table}", one=True)["c"] == 1
