# -*- coding: utf-8 -*-
"""一键重建自动化测试库（默认 health_diet_test）。

做法：
  1. 连到 MySQL 服务端（不指定库）；
  2. 删掉并重建目标库；
  3. 依次执行 schema.sql（表结构）和 seed_test.sql（最小种子数据）；
  4. 打印账号/食材数量，确认种子真的进去了。

为什么不用 `mysql < health_diet.sql`：
  - 全量 dump 有 6.7MB，含真实头像、聊天记录、训练账号，不能当测试夹具；
  - 全量 dump 没有 CREATE DATABASE / USE，空库导入会报 “No database selected”。

安全边界：
  - 目标库名必须是合法标识符；
  - 硬拒绝 health_diet（开发库）。测试脚本永远不该清空开发库。

用法：
  automation_api_requests_pytest/.venv/Scripts/python.exe database/init_test_db.py
  python database/init_test_db.py --db health_diet_test

可用环境变量覆盖连接参数：
  AUTOTEST_DB_HOST / AUTOTEST_DB_PORT / AUTOTEST_DB_USER /
  AUTOTEST_DB_PASSWORD / AUTOTEST_DB_NAME
"""

import argparse
import os
import re
import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

# Git Bash / CI 管道默认按 UTF-8 读；Windows 控制台默认 GBK。
# 统一按 UTF-8 输出，bat 里再配合 chcp 65001。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
SCHEMA_FILE = HERE / "schema.sql"
SEED_FILE = HERE / "seed_test.sql"

PROTECTED_DATABASES = {"health_diet"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


def env(name, default):
    return os.getenv(name, default)


def parse_args():
    parser = argparse.ArgumentParser(description="重建自动化测试库")
    parser.add_argument(
        "--db",
        default=env("AUTOTEST_DB_NAME", "health_diet_test"),
        help="目标库名（默认 health_diet_test，拒绝 health_diet）",
    )
    return parser.parse_args()


def check_target(name):
    if not IDENTIFIER_RE.match(name):
        sys.exit(f"非法库名：{name!r}。只允许字母、数字、下划线。")
    if name in PROTECTED_DATABASES:
        sys.exit(
            f"拒绝清空开发库 {name!r}。\n"
            "测试请用 health_diet_test；要重建开发库请手工处理 database/health_diet.sql。"
        )


def read_sql(path):
    if not path.exists():
        sys.exit(f"缺少 SQL 文件：{path}")
    return path.read_text(encoding="utf-8")


def run_script(cursor, sql, label):
    """执行整段 SQL（pymysql 开启 MULTI_STATEMENTS 后一次提交）。"""
    try:
        cursor.execute(sql)
        # 多语句会产出多个结果集，必须全部消费，否则后续语句会报
        # “Commands out of sync”。
        while cursor.nextset():
            pass
    except Exception as exc:
        sys.exit(f"执行 {label} 失败：{exc}")


def main():
    args = parse_args()
    target = args.db
    check_target(target)

    conn = pymysql.connect(
        host=env("AUTOTEST_DB_HOST", "127.0.0.1"),
        port=int(env("AUTOTEST_DB_PORT", "3306")),
        user=env("AUTOTEST_DB_USER", "root"),
        password=env("AUTOTEST_DB_PASSWORD", "123456"),
        charset="utf8mb4",
        autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS,
        connect_timeout=5,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{target}`")
            cur.execute(
                f"CREATE DATABASE `{target}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE `{target}`")

            print(f"[1/3] 建库 {target} 完成")
            run_script(cur, read_sql(SCHEMA_FILE), "schema.sql")
            print(f"[2/3] 表结构导入完成（{SCHEMA_FILE.name}）")
            run_script(cur, read_sql(SEED_FILE), "seed_test.sql")
            print(f"[3/3] 种子数据导入完成（{SEED_FILE.name}）")

            cur.execute("SELECT COUNT(*) FROM `user`")
            users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `ingredient`")
            ingredients = cur.fetchone()[0]
            cur.execute(
                "SELECT email FROM `user` WHERE email IN (%s, %s) ORDER BY id",
                ("2311697186@qq.com", "123456@qq.com"),
            )
            emails = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

    print(f"\n[完成] {target}: user={users}, ingredient={ingredients}")
    print(f"[账号] {', '.join(emails) if emails else '缺失（检查 seed_test.sql）'}")
    if users < 2 or ingredients == 0:
        sys.exit("种子数据不完整，请检查 seed_test.sql")
    print("\n下一步：")
    print(f"  set DB_NAME={target}")
    print("  cd backend && mvnw spring-boot:run")


if __name__ == "__main__":
    main()
