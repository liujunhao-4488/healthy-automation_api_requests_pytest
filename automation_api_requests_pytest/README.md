# 接口自动化测试项目 · 知识点索引

pytest + requests 写的接口自动化测试，被测系统：健康饮食后端 `http://127.0.0.1:8080/api`。

> **本文件是项目的"知识点地图"。**
> 打开 `test_cases/` 看见一堆文件、不知道哪个在讲什么的时候，先回这里查表。

---

## 一、知识点地图（按学习顺序）

| 序 | 编号 | 测试文件 | 这个文件在讲什么（人话） | 新学的核心概念 | 用例数 | 数据从哪来 |
|:--:|:--|:--|:--|:--|:--:|:--|
| 1 | `#1` 地基 | `test_auth.py` | 第一个接口测试：登录成功 / 密码错 | fixture、assert、业务 code | 2 | 代码内常量 |
| 2 | `#2` 封装 | `test_recipe_v2.py` | 把"拼URL+判code"的重复动作收进客户端 | `ApiClient`、**路径解耦** | 3 | 接口动态取 id |
| — | `#2` 对照 | `test_recipe.py` ⚠️ | 旧风格对照物，**已挂 `collect_ignore` 不参与自动跑** | 反面教材：跨层耦合 → 404 | 3 | 代码内常量 |
| 3 | `#3` 参数化 | `test_param_boundary.py` | 一条用例吃一组输入（9 登录 + 5 搜索） | `@pytest.mark.parametrize`、**边界值 / 异常值** | 16 | .py 内字面量 |
| 4 | `#3.5` DDT | `test_login_ddt.py` | 把数据搬出代码，改用外部文件 | **数据驱动**、外部文件、**fuzz 模糊测试** | 22 | JSON + CSV |
| 5 | `#3.5` 续 | `test_login_sources.py` | 换数据格式，一行业务代码都不用改 | **数据源可插拔** | 12 | YAML + Excel |
| 6 | `#3.6` 工厂 | `test_data_factory.py` | "大量数据"靠程序**生成**，不靠手写 | 笛卡尔积、边界算法、可复现 fuzz | 27 | 程序生成 |
| 7 | `#3.7` 动态 | `test_dynamic_data.py` | 数据运行时**现场取**，不写死 | DB 取数、**接口链式依赖** | 3 | MySQL / 上游接口 |
| 8 | `#3.8` 数据库 | `test_db_conn_write.py` | 数据库工具升级：连接复用 + 能写 + 有日志 | 连接复用、`execute`/`executemany`、**事务回滚** | 7 | MySQL 临时表 |
| | | | | **合计** | **92** | |

> ⚠️ = 该文件被 `conftest.py` 的 `collect_ignore` 排除，`pytest test_cases` 时不计入；想单独研究它，直接 `pytest test_cases/test_recipe.py` 点名跑。

---

## 二、反向索引：想复习哪个知识点 → 打开哪个文件

| 我想搞懂… | 打开这个文件 | 重点看哪里 |
|:--|:--|:--|
| pytest 最基础的套路（`def test_` + `assert`） | `test_auth.py` | 全篇，只有 2 条，最短最好读 |
| 什么是 fixture（`api` / `token` / `auth_headers`） | `conftest.py` | 三个 `@pytest.fixture` 函数 |
| 为什么用例不该自己拼 BASE_URL | `test_recipe.py` vs `test_recipe_v2.py` | 两个文件第 1 条用例对比着看 |
| 怎么一行断言"成功" | `common/api_client.py` | `assert_ok()` 方法 |
| `@pytest.mark.parametrize` 怎么用 | `test_param_boundary.py` | 第 1 组的 `LOGIN_CASES` 表 |
| 边界值 / 等价类怎么设计 | `test_param_boundary.py` | `LOGIN_CASES` 里超长、注入那几行 |
| 数据驱动（DDT）是什么 | `test_login_ddt.py` | 顶部注释 + `CASES` 那段循环 |
| 数据文件怎么读（4 种格式） | `common/data_loader.py` | `load_cases()` 函数 |
| **CSV 中文乱码 / BOM 坑** | `common/data_loader.py` | `utf-8-sig` 那几行 |
| "大量数据"怎么造 | `common/data_factory.py` | `cartesian` / `boundary_numbers` / `fuzz_emails` |
| 怎么从数据库取真实数据当输入 | `common/db.py` + `test_dynamic_data.py` | `query()` 用法 |
| 接口链式依赖（上一步结果喂下一步） | `test_dynamic_data.py` | `test_chain_data_from_api` |
| 数据库连接怎么复用（别每次新建） | `common/db.py` | `get_conn()` / `_IDLE_BEFORE_PING` |
| 怎么往库里写数据（造数据/清理） | `common/db.py` + `test_db_conn_write.py` | `execute` / `executemany` / `transaction()` |
| 怎么在用例里"临时替换"某个函数 | `test_db_conn_write.py` | `test_five_queries_share_one_connection` 里的 `monkeypatch` |
| 怎么让每条 SQL 都打日志、看耗时 | `pytest.ini` + `common/db.py` | `log_cli` 与 `log.info` |

---

## 三、支撑设施（不是用例，是被复用的"零件"）

```
automation_api_requests_pytest/
├── README.md            ← 你正在看的这份知识点索引
├── config.py            ← 配置中心：BASE_URL / TIMEOUT / 测试账号
├── conftest.py          ← 公共夹具：api / token / auth_headers（+ collect_ignore）
├── pytest.ini           ← pytest 运行配置（中文用例名显示等）
├── requirements.txt     ← 依赖清单
├── test_cases/          ← 测试用例（知识点地图见上表）
│   ├── test_auth.py
│   ├── test_recipe.py           ⚠️ 旧风格对照，默认不跑
│   ├── test_recipe_v2.py
│   ├── test_param_boundary.py
│   ├── test_login_ddt.py
│   ├── test_login_sources.py
│   ├── test_data_factory.py
│   ├── test_dynamic_data.py
│   └── test_db_conn_write.py
├── common/              ← 可复用零件
│   ├── api_client.py    ← 请求封装：get/post/put/delete + assert_ok
│   ├── data_loader.py   ← 统一读数据：json / csv / yaml / xlsx → list[dict]
│   ├── data_factory.py  ← 批量生成数据：组合 / 边界 / fuzz
│   └── db.py            ← MySQL 工具：连接复用 + 读/写 + 事务 + SQL 日志
└── data/                ← 外部数据文件（同一份 6 行登录数据的 4 个孪生版本）
    ├── login_cases.json
    ├── login_cases.csv
    ├── login_cases.yaml
    └── login_cases.xlsx
```

---

## 四、怎么跑

```bash
cd D:\jiankang\healthy\automation_api_requests_pytest

# 跑全套（85 条）
.venv\Scripts\python.exe -m pytest test_cases -v

# 只跑某一个知识点
.venv\Scripts\python.exe -m pytest test_cases/test_param_boundary.py -v

# 只看有哪些用例、不执行（当"活清单"用）
.venv\Scripts\python.exe -m pytest test_cases --collect-only -q

# 想看清某个用例挂在哪：-v 看名字，--tb=short 缩短报错栈
.venv\Scripts\python.exe -m pytest test_cases -v --tb=short
```

**前置条件**（后端没起会全红）：
```bash
# 1) 先确认 MySQL 在跑（3306 有监听即可）
netstat -ano | grep 3306

# 2) 启动后端 —— 必须摘掉宿主注入的 SERVER__PORT，否则端口会被覆盖成 62924 而启动失败
cd D:\jiankang\healthy\backend
env -u SERVER__PORT java -jar target/health-diet-backend-1.0-SNAPSHOT.jar > run.log 2>&1 &

# 3) 确认起在 8080（返回 401 就对了，因为没带 token）
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/api/recipe/list
```

> ⚠️ **启动后端的坑（每次都要注意）**：本机环境里有个名为 `SERVER__PORT` 的变量（**双下划线**，值随会话变化，如 62924），
> Spring Boot 的"宽松绑定"会把它当成 `server.port`，**覆盖掉 application.yml 里的 8080**，
> 然后和宿主自己占用的那个端口撞车 → `APPLICATION FAILED TO START ... Port xxxxx was already in use`。
> 解决：启动前 `env -u SERVER__PORT`（或加 `--server.port=8080`）。
> 判断是否中招：看 `run.log` 里 `Tomcat initialized with port(s): N`，N 不是 8080 就是中招了。

---

## 五、三条约定（防止以后再次迷路）

1. **命名**：新增文件用 `test_<被测对象>_<知识点>.py`，例如 `test_recipe_parametrize.py`、`test_order_ddt.py`。
   名字里带上"知识点"，光看文件名就知道它教什么。
2. **文件头**：每个测试文件第一行固定写 `# 【任务 #x：知识点】` + 一句话这个文件在证明什么。
   （多数文件已经写了，见 `test_param_boundary.py` / `test_login_ddt.py` / `test_dynamic_data.py` 的头部。）
3. **加完新文件，回来更新第一节的"知识点地图"表** —— 保持这份索引和目录同步。

---

## 六、已知的"文档 vs 实现"不一致（缺陷候选）

练习过程中实测发现的，对应路线图"失败用例比成功用例值钱"：

| # | 现象 | 涉及接口 | 记录位置 |
|:--:|:--|:--|:--|
| 1 | 文档写"无需认证"，实测无 token → 401 | `GET /recipe/search` | `test_param_boundary.py` |
| 2 | 缺 `keyword` 参数时返回 Spring 默认 400，不走统一信封 | `GET /recipe/search` | `test_param_boundary.py` |
