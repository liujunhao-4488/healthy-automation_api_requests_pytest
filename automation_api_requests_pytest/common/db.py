# common/db.py
# 【L3 动态数据】运行时直接从数据库取"真实存在的数据"当测试输入。
#
# 为什么需要它？
#   写死 id=101 的用例很脆：那行数据一被删，测试就误报红。
#   从库里取"当前真实存在的一条"当输入，测试就跟着数据一起"活"了。
#
# ============ v2 改进（对应 v1 的三个问题）============
# v1 的问题                       →  v2 的做法
#   ① 每次 query() 都 connect+close   →  连接复用：模块级缓存一条连接，闲置久了才 ping 重连
#   ② 只能 SELECT，没法造数据/清理    →  新增 execute / executemany / transaction()
#   ③ 执行了什么 SQL 完全看不见       →  每条 SQL 打日志：一行化 SQL + 参数 + 行数 + 耗时
#
# 日志怎么看：
#   · 跑 pytest 时——pytest.ini 里开了 log_cli，自动显示；
#   · 在 pytest 外单独跑脚本时——先 `logging.basicConfig(level=logging.INFO)`。
#
# ============ 纪律（v2 新增了写能力，所以纪律更重要）============
#   1. 造数据只用自己的临时命名（tmp_ 前缀），用完必须清理（try/finally 或 teardown）。
#   2. 不要 DELETE / UPDATE 业务表里的既有数据——那是在破坏别人的测试环境。
#   3. 写操作在日志里故意用 WARNING 级别，让你一眼看见"谁动了数据"。

import atexit
import contextlib
import logging
import time

import pymysql

log = logging.getLogger("db")

DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",   # 与 backend/application.yml 一致
    "database": "health_diet",
    "charset": "utf8mb4",
}


# ==================== ① 连接复用 ====================
# 整个测试进程共用一条连接，省掉每次握手的开销（TCP + 认证）。
# 代价：连接是有状态的，多线程并发共用会串味 —— 本项目的 pytest 是单进程顺序跑，安全。
_conn = None
_last_used = 0.0
_IDLE_BEFORE_PING = 30.0   # 秒。闲置超过这么久才 ping 一次，避免每次调用都白跑一个来回


def get_conn():
    """拿可复用的连接：没有就新建；闲置太久了才 ping 一下确认还活着。"""
    global _conn, _last_used
    now = time.monotonic()

    if _conn is None:
        _conn = pymysql.connect(**DB, autocommit=True)
        log.debug("新建数据库连接 %s:%s/%s", DB["host"], DB["port"], DB["database"])
    elif now - _last_used > _IDLE_BEFORE_PING:
        # 服务端有 wait_timeout，闲置久了会单方面断开。
        # ping(reconnect=True) = 探活，断了就悄悄重连，避免"连接已失效"这种偶发报错。
        _conn.ping(reconnect=True)

    _last_used = now
    return _conn


def close_conn():
    """主动收尾（进程退出时会自动调用一次）。"""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
        log.debug("数据库连接已关闭")


atexit.register(close_conn)


# ==================== ③ 日志辅助 ====================
def _one_line(sql):
    """多行 SQL 折成一行 —— 否则日志会被 SQL 换行刷成一大片，没法看。"""
    return " ".join(sql.split())


def _ms(t0):
    return (time.perf_counter() - t0) * 1000


# ==================== 读 ====================
def query(sql, args=None, one=False):
    """SELECT → list[dict]（每行一个字典，像 JSON 那样取字段）。

    one=True 时只返回第一行（dict），查不到返回 None——适合"只要一条"的场景。
    """
    t0 = time.perf_counter()
    with get_conn().cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, args or ())
        rows = cur.fetchone() if one else list(cur.fetchall())

    n = (0 if rows is None else 1) if one else len(rows)
    log.info("SELECT %s | args=%s | rows=%d | %.1fms", _one_line(sql), args or (), n, _ms(t0))
    return rows


# ==================== ② 写 ====================
def execute(sql, args=None):
    """INSERT / UPDATE / DELETE → 返回受影响行数。

    连接是 autocommit 的，所以**执行即生效**。造的数据请自己负责清理，
    或者用下面的 transaction() 让它在异常时自动回滚。
    """
    t0 = time.perf_counter()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            affected = cur.execute(sql, args or ())
    except Exception:
        log.exception("WRITE 失败 %s | args=%s", _one_line(sql), args or ())
        raise

    # 故意用 WARNING 级别：写操作在日志里要显眼
    log.warning("WRITE %s | args=%s | affected=%d | %.1fms", _one_line(sql), args or (), affected, _ms(t0))
    return affected


def executemany(sql, rows):
    """批量写（一条 SQL × 多组参数）→ 返回受影响行数合计。"""
    rows = list(rows)
    t0 = time.perf_counter()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            affected = cur.executemany(sql, rows)
    except Exception:
        log.exception("BULK 失败 %s | 参数组数=%d", _one_line(sql), len(rows))
        raise

    log.warning("BULK %s | 参数组数=%d | affected=%d | %.1fms", _one_line(sql), len(rows), affected, _ms(t0))
    return affected


@contextlib.contextmanager
def transaction():
    """事务上下文：正常结束自动提交，出异常自动回滚。

    为什么需要它？"造数据 → 验证 → 撤销"这个套路里，撤销最容易忘。
    把它交给事务，就算用例中途挂了，数据也不会留在地上。

    用法：
        with transaction() as cur:
            cur.execute("insert into tmp_x ...")
            assert query("select count(*) from tmp_x", one=True)["count(*)"] == 1
            raise RuntimeError("故意抛错，整段回滚")   # 等价于"什么都没发生"

    原理：pymysql 的 begin() 会显式开启事务，此时 autocommit 被挂起，
          直到 commit / rollback —— 所以这是真事务，不是摆设。
    """
    conn = get_conn()
    conn.begin()
    log.info("BEGIN 事务")
    try:
        with conn.cursor() as cur:
            yield cur
    except Exception:
        conn.rollback()
        log.warning("ROLLBACK 事务（发生异常，已撤销全部改动）")
        raise
    else:
        conn.commit()
        log.info("COMMIT 事务")
