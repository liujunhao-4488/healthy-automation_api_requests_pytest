# config.py
# 作用：把"会变的东西"集中放一个地方。
# 类比：做菜时把"火候、盐量"写在一张纸条上，而不是每道菜都重新记一遍。
#
# 2026-10-23 改造：全部支持环境变量覆盖。
#   默认值仍然保证"本机 clone 下来能跑"，但换机器/CI 时**不用改代码**：
#       set AUTOTEST_BASE_URL=http://ci-host:8080/api
#       set AUTOTEST_DB_NAME=health_diet_test
#       set AUTOTEST_DB_PASSWORD=***
#   环境变量没设时才用下面的默认值。

import os


def _env(name, default):
    return os.getenv(name, default)


def _env_int(name, default):
    return int(os.getenv(name, str(default)))


# 后端地址。注意 API.md 里说前缀是 /api，所以 BASE_URL 已经带上了。
BASE_URL = _env("AUTOTEST_BASE_URL", "http://127.0.0.1:8080/api")

# 算法服务（Flask）地址。
# 它和 Java 后端是**两个进程、两个端口**，而且没有 /api 之外的统一前缀约定：
# 推荐接口是 /api/recommend/*，知识库检索是 /api/kb/*。
# ⭐ 知识库检索为什么要单独配一个地址：RAG 的召回测试**直连这里**，
#    不经 Java、不用登录拿 token、不用同时起两个服务 —— 一条链路直达，
#    测的才是"检索本身"，而不是"Java 转发得好不好"。
KB_BASE_URL = _env("AUTOTEST_KB_BASE_URL", "http://127.0.0.1:5000")

# 每个请求最多等多久（秒）。防止某个接口卡死时测试一直挂起。
TIMEOUT = _env_int("AUTOTEST_TIMEOUT", 10)

# 测试用的主登录账号。
# 这个账号**不再要求库里预先存在**：conftest 的环境预检会先尝试登录，
# 账号不存在就用 /auth/register 自动创建（见 common/accounts.py）。
TEST_USER = {
    "email": _env("AUTOTEST_EMAIL", "2311697186@qq.com"),
    "password": _env("AUTOTEST_PASSWORD", "123456"),
}

# 自动补建主账号时用的用户名。邮箱已存在时不会用到它。
# 故意和 seed_test.sql 里的 'autotest_primary' 不同：
#   预检用「测试库里的 username == 后端登录返回的 username」判断后端有没有连错库。
#   如果补建也用同一个名字，开发库空库自动补建时就会“碰巧对上”，检查失效。
TEST_USERNAME = _env("AUTOTEST_USERNAME", "autotest_primary_auto")

# 登录/注册数据驱动用例依赖的"库里已存在账号"（data/login_cases.yaml）。
# 它由 database/seed_test.sql 创建；如果没跑种子，conftest 也会自动补建。
SEED_LOGIN_USER = {
    "username": "autotest_login",
    "email": "123456@qq.com",
    "password": "123456",
}

# 数据库连接参数 —— common/db.py 直连库时用。
#
# ⚠️ 默认库名是 **health_diet_test**，不是开发库 health_diet。
#    测试会删临时账号、写健康档案；默认指向开发库等于把别人的环境当草稿纸。
#    跑测试时后端也必须连同一个库：
#        set DB_NAME=health_diet_test
#        cd backend && mvnw spring-boot:run
#    后端和测试库不一致时，环境预检会直接中止并提示（见 conftest.py）。
DB = {
    "host": _env("AUTOTEST_DB_HOST", "127.0.0.1"),
    "port": _env_int("AUTOTEST_DB_PORT", 3306),
    "user": _env("AUTOTEST_DB_USER", "root"),
    "password": _env("AUTOTEST_DB_PASSWORD", "123456"),
    "database": _env("AUTOTEST_DB_NAME", "health_diet_test"),
    "charset": "utf8mb4",
}

# 是否强制要求 MySQL 可用（默认 1）。
#   1 = 全套跑之前检查测试库，缺库直接中止并给出建库命令；
#   0 = 只跑纯接口（后端连远程库/别人的环境），直接访问 DB 的用例自动 skip。
REQUIRE_DB = _env("AUTOTEST_REQUIRE_DB", "1") == "1"
