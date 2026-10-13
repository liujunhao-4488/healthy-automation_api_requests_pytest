# config.py
# 作用：把"会变的东西"集中放一个地方。
# 类比：做菜时把"火候、盐量"写在一张纸条上，而不是每道菜都重新记一遍。
# 以后后端换电脑/换端口，只改这里，所有测试自动跟着变。

# 后端地址。注意 API.md 里说前缀是 /api，所以 BASE_URL 已经带上了。
BASE_URL = "http://127.0.0.1:8080/api"

# 每个请求最多等多久（秒）。防止某个接口卡死时测试一直挂起。
TIMEOUT = 10

# 测试用的登录账号。这是库里已存在的示例账号（见 API.md 第 4.2 节）。
# 后面"登录 fixture"会拿它去换 token。
TEST_USER = {
    "email": "2311697186@qq.com",
    "password": "123456",
}

# 数据库连接参数 —— common/db.py 直连库时用（跟后端连的是同一个库）。
#
# 为什么放这儿？因为它也是"会变的东西"：换台电脑、同事 clone 你的项目、
# 后端换库名/改密码，全都要动。判断标准一句话：
#   别人拿我这个项目去跑，这行要不要改？要改 → 进 config。
#
# 改这里一处，common/db.py 一个字都不用动。
DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",   # 与 backend/application.yml 一致
    "database": "health_diet",
    "charset": "utf8mb4",
}
