# 接口自动化测试项目 · 知识点索引

pytest + requests 写的接口自动化测试，被测系统：健康饮食后端 `http://127.0.0.1:8080/api`。

> **本文件是项目的"知识点地图"。**
> 打开 `test_cases/` 看见一堆文件、不知道哪个在讲什么的时候，先回这里查表。

> ⚠️ **历史记录提示：§一 / §二 的表格是重构前的学习向记录**（合计 151 条，
> `recipe/`、`toolbox/test_data_factory.py` 等文件已删除），**只作演进史参考，不要当当前清单用**。
>
> **当前真实状态（2026-10-23 `--collect-only` 实测）**：
> - 用例 **293 条**：AI 助手 221 / health 35 / user 15 / auth 15 / toolbox 7
> - 目录：`ai_assistant/` `auth/` `health/` `toolbox/` `user/` + `api/` `common/` `config/` `data/` `tools/`
> - 后端接口：控制器实测 **78 个**（方法级）；已覆盖 **15 个**（auth 2 / user 2 / health 5 / assistant 6，含 SSE）
> - `api/` 层封装 18 个方法 = 15 个后端接口 + 3 个算法服务（KB）接口
> - 覆盖矩阵见 `docs/接口覆盖矩阵.md` 顶部；AI 助手的来龙去脉见 `docs/AI助手模块-迭代记录.md`
> - 下面的**目录树**（§三）已按当前结构更新，可以照着找文件。

---

## 一、知识点地图（按学习顺序）

> ⚠️ 下表是 2026-09 的学习顺序记录，列出的 `recipe/`、`toolbox/test_data_factory.py` 等文件已删除，
> 「合计 151」也早已过期。**当前用例清单见 §三 的 `test_cases/`**。

| 序 | 编号 | 测试文件 | 这个文件在讲什么（人话） | 新学的核心概念 | 用例数 | 数据从哪来 |
|:--:|:--|:--|:--|:--|:--:|:--|
| 1 | `#4.2` 登录（合并） | `auth/test_login.py` | 登录接口的 4 个"写法版本"合并成一个文件：地基 → 参数化 → 数据驱动 → fuzz | fixture、`assert_ok`、`parametrize`、**DDT 四层数据源**、fuzz | 45 | 代码内 + JSON/CSV/YAML/Excel |
| 2 | `#2` 封装 | `recipe/test_recipe_v2.py` | 把"拼URL+判code"的重复动作收进客户端 | `BaseApiClient`、**路径解耦** | 3 | 接口动态取 id |
| 2b | `#2b` 接口层 | `api/`（**不是测试文件**） | 把**接口路径**从用例里搬进专门一层：用例只认方法名，不认 URL | **接口封装层**、**单一底座**、逃生舱 `raw_get` | — | — |
| — | `#2` 对照 | `recipe/test_recipe.py` ⚠️ | 旧风格对照物，**已挂 `collect_ignore` 不参与自动跑** | 反面教材：跨层耦合 → 404 | 3 | 代码内常量 |
| 3 | `#4.2b` 健壮性 | `recipe/test_recipe_search.py` | 搜索接口的关键词健壮性 + 2 条"文档与实现不一致" | 注入 / 超长 / 空值的"不崩"断言 | 7 | .py 内字面量 |
| 4 | `#3.6` 工厂 | `toolbox/test_data_factory.py` | "大量数据"靠程序**生成**，不靠手写 | 笛卡尔积、边界算法、可复现 fuzz | 27 | 程序生成 |
| 5 | `#3.7` 动态 | `toolbox/test_dynamic_data.py` | 数据运行时**现场取**，不写死 | DB 取数、**接口链式依赖** | 3 | MySQL / 上游接口 |
| 6 | `#3.8` 数据库 | `toolbox/test_db_conn_write.py` | 数据库工具升级：连接复用 + 能写 + 有日志 | 连接复用、`execute`/`executemany`、**事务回滚** | 7 | MySQL 临时表 |
| 7 | `#4.1a` 写操作 | `health/test_health_info.py` | 第一次测**写**接口（健康档案）：写完读回来对账，测完自动还原 | **写读回环**、**yield 夹具**、**顺序依赖假失败** | 11 | 接口动态取值 |
| 8 | `#4.1b` 写操作 | `health/test_health_goal.py` | 同上，但测的是饮食目标；**夹具只备份自己那一份** | **夹具粒度匹配用例需求** | 7 | 接口动态取值 |
| 9 | `#4.2` 注册 | `auth/test_register.py` | 注册接口的正常 + 异常：拒 4 类非法邮箱，成功路径带唯一值与清理 | **唯一值防"二次运行冲突"**、yield 清理夹具 | 6 | .py 内 + 时间戳生成 |
| 10 | `#4.3` 用户资料 | `user/test_user_profile.py` | 单例资源的读写：鉴权 6 型、**字段白名单**、唯一性边界、**越权 4 个入口逐个试** | **单例还原夹具**、JWT 篡改三连、**交叉比对证隔离** | 35 | 接口动态取值 + MySQL 对质 |
| | | | | **合计** | **151** | |

> **2026-09-29 合并说明**：原 `auth/` 下的 `test_auth.py` / `test_param_boundary.py` /
> `test_login_ddt.py` / `test_login_sources.py` 四个文件（共 52 条）已合并进 `auth/test_login.py`。
> 理由：它们测的是**同一个接口**，只是四个"写法版本"。合并后按接口就能找全用例——
> 原来那份"按知识点切"的进化史没有丢，变成了同一文件里的第 1~4 组。
> 其中原来混在 `test_param_boundary.py` 里的 **7 条 `/recipe/search` 用例已归位到 `recipe/test_recipe_search.py`**
> （那个文件其实横跨两个资源，不符合"按资源切文件"）。


> ⚠️ = 该文件被 `conftest.py` 的 `collect_ignore` 排除，`pytest test_cases` 时不计入；
> 想单独研究它，直接 `pytest test_cases/recipe/test_recipe.py` 点名跑。

---

## 二、反向索引：想复习哪个知识点 → 打开哪个文件

| 我想搞懂… | 打开这个文件 | 重点看哪里 |
|:--|:--|:--|
| pytest 最基础的套路（`def test_` + `assert`） | `auth/test_login.py` | 第 1 组，只有 2 条，最短最好读 |
| 什么是 fixture（`api` / `token` / `auth_headers`） | `conftest.py` | 三个 `@pytest.fixture` 函数 |
| 为什么用例不该自己拼 BASE_URL | `recipe/test_recipe.py` vs `recipe/test_recipe_v2.py` | 两个文件第 1 条用例对比着看 |
| **接口路径为什么只能写在一个地方** | `api/__init__.py` | 头部「为什么要多这一层」+ `Api` 类的聚合写法 |
| **一个接口怎么变成"一个方法"** | `api/user_api.py` | `get_profile` / `update_profile`（契约坑全写在 docstring 上） |
| **路径里带变量的接口怎么封装** | `api/recipe_api.py` | `detail(recipe_id)` —— 变量走参数，不写死在方法里 |
| **接口类的底座为什么只有一个 `BaseApiClient`** | `api/base_api_client.py` | 头部注释（讲清了它是由 `ApiClient` + `BaseApi` 合并来的，以及合并前后各要理解几个概念） |
| **封装层遇到"故意打非法路径"怎么办** | `api/__init__.py` + `user/test_user_profile.py` | `raw_get()` 逃生舱 ↔ `test_no_id_based_profile_route` 的 404 探针 |
| 怎么一行断言"成功" | `api/base_api_client.py` | `assert_ok()` 方法 |
| `@pytest.mark.parametrize` 怎么用 | `auth/test_login.py` | 第 2 组的 `LOGIN_CASES` 表 |
| 边界值 / 等价类怎么设计 | `auth/test_login.py` | `LOGIN_CASES` 里超长、注入那几行 |
| 数据驱动（DDT）是什么 | `auth/test_login.py` | 第 3 组顶部注释 + `CASES` 那段循环 |
| 数据文件怎么读（4 种格式） | `common/data_loader.py` | `load_cases()` 函数 |
| **CSV 中文乱码 / BOM 坑** | `common/data_loader.py` | `utf-8-sig` 那几行 |
| "大量数据"怎么造 | `common/data_factory.py` | `cartesian` / `boundary_numbers` / `fuzz_emails` |
| 怎么从数据库取真实数据当输入 | `common/db.py` + `toolbox/test_dynamic_data.py` | `query()` 用法 |
| 接口链式依赖（上一步结果喂下一步） | `toolbox/test_dynamic_data.py` | `test_chain_data_from_api` |
| 数据库连接怎么复用（别每次新建） | `common/db.py` | `get_conn()` / `_IDLE_BEFORE_PING` |
| 怎么往库里写数据（造数据/清理） | `common/db.py` + `toolbox/test_db_conn_write.py` | `execute` / `executemany` / `transaction()` |
| 怎么在用例里"临时替换"某个函数 | `toolbox/test_db_conn_write.py` | `test_five_queries_share_one_connection` 里的 `monkeypatch` |
| 怎么让每条 SQL 都打日志、看耗时 | `pytest.ini` + `common/db.py` | `log_cli` 与 `log.info` |
| **怎么把接口响应打印得好看（每次都能看到返回内容）** | `test_cases/toolbox/logger.py` | `log_response(resp)` / `format_response()` |
| **为什么日志在 pytest 里会被打两遍** | `test_cases/toolbox/logger.py` | `get_logger()` 里 `_IN_PYTEST` 那段注释（`propagate=False` 反被 pytest 补挂一个 handler） |
| 怎么证明"写接口"真的写进去了 | `health/test_health_info.py` | `test_write_info_then_read_back`（写读回环） |
| 用例会改真实数据，怎么收场 | `health/test_health_info.py` / `health/test_health_goal.py` | `info_env` / `goal_env` 夹具（yield 前 setup / 后 teardown） |
| 某个接口到底哪些字段必填 | `health/test_health_info.py` / `health/test_health_goal.py` | `INFO_REQUIRED` / `GOAL_REQUIRED` 表 |
| **一个模块为什么要拆成两个文件** | `health/test_health_info.py` vs `health/test_health_goal.py` | 两个文件的头部注释 + 夹具写法对比 |
| **同一个接口为什么要合并成一个文件** | `auth/test_login.py` | 头部"为什么合并"注释 + 第 1~4 组的编排 |
| **注册用例怎么避免"跑第二次就红"** | `auth/test_register.py` | `new_user` 夹具：时间戳唯一值 + yield 清理 |
| **"期望失败"的用例为什么不能用 `assert_ok`** | `auth/test_register.py` vs `auth/test_login.py` | 前者手写三层断言，后者用 `assert_ok` |
| **顺序依赖的"假失败"怎么破** | `health/test_health_info.py` | `test_update_time_refreshed_on_write` 的 docstring（撞秒坑） |
| **跨目录同名文件为什么会让收集直接中断** | 本节第五节约定 7 | `import file mismatch` 与 `__init__.py` 解法 |
| **怎么测"拿别人的数据"（越权 / IDOR）** | `user/test_user_profile.py` | 组 5：`PROBE_POSITIONS`（query/header 塞 id）+ 组 1 的 JWT 篡改三连 |
| **哪些字段传了能改、哪些传了等于白传** | `user/test_user_profile.py` | `test_update_ignores_non_editable_fields` |
| **怎么伪造 token 冒充别人** | `user/test_user_profile.py` | `_tamper_signature` / `_tamper_subject` / `_tamper_alg_none` |
| **"单例资源"（改它=改全局状态）怎么收场** | `user/test_user_profile.py` | `restore_profile` 夹具（对比 health 的 `info_env`） |
| **只改一个字段，别的会不会被冲掉** | `user/test_user_profile.py` | `test_update_single_field_keeps_others`（局部更新 vs 全量覆盖） |
| **怎么写"期望失败"的边界用例** | `user/test_user_profile.py` | 组 4：手写 status_code + code + message 三层断言 |
| **`%` 在 SQL 里被 pymysql 当成占位符** | 本节第六节 | `like 'tmp\_%%'` 要写成参数化的 `%s` |
| **报告怎么看？失败了怎么查？** | `docs/Allure报告-使用说明.md` | 六个视图各回答什么问题、单条用例详情页里有什么 |
| **请求/响应原文去哪看** | `docs/Allure报告-使用说明.md` §四决定 3 | 每次 HTTP 交互自动贴成两个附件；控制台只留一行摘要 |
| **报告里的层级和严重级别是谁打的** | `common/allure_helper.py` | `derive_labels()` —— 按目录/文件名推，**不用给用例加装饰器** |
| **为什么报告目录不写在 pytest.ini 里** | `conftest.py` 的 `pytest_configure` | 相对路径坑 + 没装 allure 时不该把全场用例带崩 |
| **报告里的 token 怎么变 `***` 了** | `common/allure_helper.py` | `_mask_header()` / `_mask_value()`；要明文看就设 `ALLURE_NO_MASK=1` |
| **红的归类（后端挂了 / 断言不符 / 已知缺陷）** | `config/allure_categories.json` | 五条规则，先匹配先算 |


---

## 三、支撑设施（不是用例，是被复用的"零件"）

```
automation_api_requests_pytest/
├── README.md            ← 你正在看的这份知识点索引
├── config/              ← 配置中心：BASE_URL / TIMEOUT / 测试账号（config.py 里）
│   └── allure_categories.json ← 报告里的缺陷分类规则（后端挂了 / 断言不符 / 已知缺陷…）
├── conftest.py          ← 公共夹具：api / token / auth_headers
│                          另外：环境预检（MySQL → 后端 → 算法服务，缺一个就中止整场）、
│                          Allure 的结果目录 / 层级标签 / 环境信息也在这里装配
├── api/                 ← 【接口封装层】一个接口 = 一个方法，**接口路径只写在这一层**
│   ├── __init__.py      ← `Api` 聚合同入口：自己继承 BaseApiClient，把 auth / user / health / assistant / kb 挂成属性
│   ├── base_api_client.py ← 【唯一底座】接口类继承它，就有 get/post/put/delete + assert_ok
│   ├── auth_api.py      ← POST /auth/login、/auth/register
│   ├── user_api.py      ← GET / PUT /user/profile
│   ├── health_api.py    ← GET/POST /health/info、GET /health/history、GET/POST /health/goal
│   ├── assistant_api.py ← POST /assistant/chat、/assistant/chat/stream、会话增删查
│   └── kb_api.py        ← 算法服务（Flask）的 /api/kb/search、/api/kb/stats、/api/kb/reload
├── docs/
│   ├── 接口覆盖矩阵.md   ← 施工图：后端 78 个接口的覆盖状态 + 优先级排序
│   ├── 接口自动化-缺口清单.md ← 对照标准框架的能力缺口与 P0/P1/P2 排期
│   └── Allure报告-使用说明.md ← 报告怎么看 / 怎么跑 / 为什么这么集成
├── pytest.ini           ← pytest 运行配置（pythonpath / 中文用例名显示 / SQL 日志）
├── requirements.txt     ← 依赖清单
├── test_cases/          ← 测试用例，按业务模块分目录（合计 293 条，2026-10-23 收集数）
│   ├── ai_assistant/    ← /assistant/* + 算法服务 RAG                  ★ 已覆盖（221 条）
│   │   ├── test_assistant_结构鉴权.py            11
│   │   ├── test_assistant_安全拦截.py            24
│   │   ├── test_assistant_意图标签.py            31
│   │   ├── test_assistant_意图识别.py            10
│   │   ├── test_assistant_越狱.py                21
│   │   ├── test_assistant_注入.py                13
│   │   ├── test_assistant_上下文.py              5
│   │   ├── test_assistant_流式.py                9
│   │   ├── test_assistant_越权.py                5
│   │   ├── test_assistant_通用问题不追问档案.py   3
│   │   ├── test_assistant_RAG召回.py             80
│   │   └── test_assistant_RAG生成.py             9
│   ├── auth/            ← /auth/*                                    ★ 已覆盖（15 条）
│   │   ├── test_login.py                         6
│   │   └── test_register.py                      9
│   ├── health/          ← /health/*                                  ★ 已覆盖（35 条）
│   │   ├── test_health_info.py                   21
│   │   └── test_health_goal.py                   14
│   ├── user/            ← /user/*                                    ★ 已覆盖（15 条）
│   │   └── test_user_profile.py                  15
│   └── toolbox/         ← 工具零件自测（不对应业务接口）             7 条
│       └── test_data_loader.py                   ← Excel 多工作表加载
├── common/              ← 可复用零件（与"接口"无关的通用工具）
│   ├── accounts.py      ← 账号自愈：测试账号缺失/密码不符时自动补建
│   ├── data_loader.py   ← 统一读数据：json / csv / yaml / xlsx → list[dict]
│   ├── data_factory.py  ← 批量生成数据：组合 / 边界 / fuzz
│   ├── db.py            ← MySQL 工具：连接复用 + 读/写 + 事务 + SQL 日志
│   ├── eval_record.py   ← AI 评测留痕（旁路，不影响断言结果）
│   ├── logger.py        ← 日志：控制台一行摘要 / 文件留全量 / 顺手贴进 Allure
│   └── allure_helper.py ← 【Allure 唯一出口】请求响应附件、脱敏、层级标签、环境信息
├── tools/               ← 辅助脚本（**不是用例**：产出数字/清单，不产出红绿）
│   ├── smoke_check.py      ← 核心链路冒烟
│   ├── eval_runner.py      ← 离线算 AI 评测指标（改口径不重跑模型）
│   ├── collect_judge_samples.py / judge_faithfulness.py ← LLM-as-Judge 采样与校准
│   ├── followup_probe.py / memory_probe.py ← 多轮追问、上下文集探针
│   ├── latency_report.py   ← 拿提问集跑一遍，量耗时并导出 Excel
│   ├── jailbreak_report.py ← 红队对抗：跑越狱样本集，算攻破率并导出 Excel
│   ├── run_tests.py        ← 跑 pytest 并把输出写文件（本机抓不到 stdout 的兜底）
│   ├── allure_report.py    ← 把结果渲染成 Allure 网页（--run 可顺手跑一轮）
│   ├── allure_selftest/    ← 故意做红的自检用例（只验报告本身对不对）
│   └── clean_artifacts.py  ← 清理 logs/runs 与 reports 的旧文件（默认演习，加 --yes 才真删）
└── data/                ← 外部数据文件（同一份 6 行登录数据的 4 个孪生版本）
    ├── login_cases.json
    ├── login_cases.csv
    ├── login_cases.yaml
    └── login_cases.xlsx
```

> **用例 vs 报告**：`test_cases/` 产出红绿，用来守门；`tools/` 产出数字，用来做决策。
> 混在一起的典型错法是把"耗时不超过 3 秒"写成 assert —— 它会随机变红。

---

## 四、怎么跑

```bash
cd D:\jiankang\healthy\automation_api_requests_pytest

# 0) 首次/换机器：重建独立测试库（默认 health_diet_test，不会碰开发库 health_diet）
..\database\rebuild_test_db.bat

# 0.1) 后端必须连同一个测试库（另开终端）
#      set DB_NAME=health_diet_test
#      cd ..\backend && mvnw spring-boot:run
#      后端默认仍连 health_diet；忘了设置时环境预检会直接中止并提示。

# 跑全套（293 条收集数；通过 / 跳过 / xfail 以本次运行结果为准）
# 注1：health 早先的 4 条"缺陷固化"用例已在后端修复后转正，现在是正式断言。
# 注2：user 仍有 1 条 xfail 钉住已知缺陷 #9（PUT 后 update_time 不刷新），
#      后端修好后会变 XPASS，届时摘掉 @pytest.mark.xfail。
# 注3：AI 助手的 skip 分两类：数据集里"无观测点 / 样本不适用"的主动跳过，
#      以及 known_defect 的 xfail —— 两者都不是回归失败（见 docs/AI助手模块-迭代记录.md）。
.venv\Scripts\python.exe -m pytest test_cases -v

# 只跑某一个模块（按目录跑，最常用）
.venv\Scripts\python.exe -m pytest test_cases/auth -v

# 只跑某一个文件
.venv\Scripts\python.exe -m pytest test_cases/auth/test_login.py -v

# 只看有哪些用例、不执行（当"活清单"用）
.venv\Scripts\python.exe -m pytest test_cases --collect-only -q

# 想看清某个用例挂在哪：-v 看名字，--tb=short 缩短报错栈
.venv\Scripts\python.exe -m pytest test_cases -v --tb=short

# 跑"报告"（不是用例，不产红绿）：AI 助手提问集的耗时，导出 reports/*.xlsx
.venv\Scripts\python.exe tools/latency_report.py --limit 5

# 清理产物堆积：logs/runs 保留 30 天、reports 保留 90 天
# （默认只演习列清单，确认后加 --yes 才真删；每个目录至少留最新 1 个）
.venv\Scripts\python.exe tools/clean_artifacts.py
```

**看 Allure 报告**（跑完用例才会有所得看；完整说明见 `docs/Allure报告-使用说明.md`）：

```bash
# 两步：先跑用例（顺带产出 reports/allure-results/），再渲染成网页并打开
.venv\Scripts\python.exe -m pytest test_cases -q
.venv\Scripts\python.exe tools/allure_report.py --open

# 一条命令搞定：跑全套 → 清旧结果 → 出报告 → 打开浏览器
.venv\Scripts\python.exe tools/allure_report.py --run --open

# 只跑一个模块并出报告（--run 后面的参数原样透给 pytest）
.venv\Scripts\python.exe tools/allure_report.py --run test_cases/auth -q --open

# 只看"严重级别 = critical"（登录 / 用户资料，挂了说明鉴权和越权出问题）
.venv\Scripts\python.exe -m pytest test_cases --allure-severities=critical -q

# 只跑某个业务功能（层级标签是自动打的，用例不用改）
.venv\Scripts\python.exe -m pytest test_cases --allure-features="AI 助手" -q
```

> ⚠️ **别直接双击 `reports/allure-report/index.html`** —— 报告是纯前端 + 一堆 JSON，
> `file://` 下读本地 JSON 会被浏览器拦掉，页面一片空白。必须 `--open` 起个本地服务。
>
> 报告里的"请求/响应"是自动贴的（`api/base_api_client.py` 一处埋点全覆盖），
> 里面的 `Authorization` 和 `password` **默认打码**；要明文排查就设 `$env:ALLURE_NO_MASK=1`。
>
> 第一次用还缺两样东西：`pip install -r requirements.txt`（拿到 `allure-pytest`）
> 和 Allure 命令行工具（解压到 `tools/allure-cli/`，见 `docs/Allure报告-使用说明.md` 第二节）。

**前置条件**（三个依赖缺一个，环境预检会直接中止，不会跑用例）：
```bash
# 1) 先确认 MySQL 在跑（预检会执行 SELECT 1，并校验 health_diet_test 可读）
netstat -ano | grep 3306

# 2) 启动后端 —— 必须摘掉宿主注入的 SERVER__PORT，否则端口会被覆盖成 62924 而启动失败
#    跑自动化时必须同时指定测试库，否则测试对账会打到你没在用的库
export DB_NAME=health_diet_test
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

> ⚠️ **测试库必须前后端一致**：测试默认连 `health_diet_test`，后端默认连 `health_diet`。
> 启动后端时忘了 `set DB_NAME=health_diet_test`，环境预检会发现“测试库里没有后端登录返回的 userId/username”
> 并中止，提示你补上这个变量 —— 不会再出现“用例全绿但实际改的是开发库”。

> ⚠️ **在 AI 工具环境里跑测试还要摘代理**：工具环境注入了 `HTTP_PROXY/HTTPS_PROXY`，
> `requests` 默认会走它，连 `127.0.0.1:8080` 会得到 **502**（看起来像后端挂了）。
> 跑之前先 `unset HTTP_PROXY HTTPS_PROXY` + `export NO_PROXY=127.0.0.1,localhost`。
> 你在 PyCharm 里自己跑没有这个问题。

---

## 五、十二条约定（防止以后再次迷路）

1. **命名**：新增文件用 `test_<被测对象>_<知识点>.py`，例如 `test_recipe_parametrize.py`、`test_order_ddt.py`。
   名字里带上"知识点"，光看文件名就知道它教什么。
2. **文件头**：每个测试文件第一行固定写 `# 【任务 #x：知识点】` + 一句话这个文件在证明什么。
   （多数文件已经写了，见 `auth/test_login.py` / `recipe/test_recipe_search.py` / `toolbox/test_dynamic_data.py` 的头部。）
3. **加完新文件，回来更新第一节的"知识点地图"表** —— 保持这份索引和目录同步。
4. **补业务用例之前，先看 `docs/接口覆盖矩阵.md`** —— 那是施工图（77 个接口谁覆盖了、谁没覆盖、先打哪个）。
   每补完一个接口，回矩阵把 ⬜ 改成 ✅。**别凭感觉随机挑接口写。**
5. **拆分维度：按"资源"切文件，不按"知识点"切。**
   一个文件对应一个接口/资源（`health/test_health_info.py` = `/health/info`，`health/test_health_goal.py` = `/health/goal`），
   知识点靠文件头注释和函数名表达。配套原则：**夹具的粒度要匹配用例的需求**——
   只测 A 资源的用例，夹具不该顺手去动 B 资源（白花请求，还多一份数据风险）。
6. **目录按"模块"分，文件按"资源"切。** `test_cases/` 的下一级目录名 = URL 前缀
   （`auth/` 放 `/auth/*` 的用例，`health/` 放 `/health/*`…），想找某个接口的用例直接进对应目录。
   不对应任何业务接口的"工具零件自测"统一放 `toolbox/`（数据工厂、数据库工具、动态取数）。
   新增模块时就新建一个目录，别把文件堆在 `test_cases/` 根下。
7. **文件切多细：看这个模块的用例量，不是看知识点数量。**（2026-09-29 定）
   - 模块用例 **< 40 条或接口 < 5 个** → **一个模块一个文件**就够（`recipe/test_recipe_v2.py`）。
   - 模块内部**有多个独立资源、各自用例够多** → **按资源切**（`health/` → info / goal 两个文件）。
   - 单文件**超过约 300 行 / 40 个函数**就拆，否则找一条用例要翻半天。
   - ⚠️ 跨目录**文件名必须唯一**（`user/test_profile.py` 和 `admin/test_profile.py` 会撞车，实测报
     `import file mismatch` 直接中断收集）。解法：要么保证 basename 唯一（当前 10 个文件都满足），
     要么给每个目录加 `__init__.py`（已实测可解）。
   - ⚠️ 同一模块**不要同时存在两份测同一个接口的文件**（会重复收集、重复写数据）。要留对照就把旧的挂进 `collect_ignore`。
8. **合并/拆分后，必须跑这两条命令对账**（2026-09-29 定）：
   ```bash
   .venv\Scripts\python.exe -m pytest test_cases --collect-only -q   # 总数应与改动前完全一致
   .venv\Scripts\python.exe -m pytest test_cases -q                  # 通过/失败数也应完全一致
   ```
   **一条不多、一条不少**才算搬家成功。只看"没报错"不够——少收集了几条 pytest 不会提醒你。
9. **报缺陷之前，先回答一句："我说'应该这样'，依据是什么？"**（2026-09-30 定）
   依据只能是三者之一：① 文档/需求/前端页面写明了的 ② 表结构、字段语义明确表达的
   ③ 团队已经按某个标准修过同类问题（先例）。
   三者都不是 → 记成「观察点」，**别写进缺陷单**。判缺陷用的是**需求**这把尺子，不是"我的直觉"。
   > 反面教材（我自己踩的）：把"`PUT /user/profile` 传 `email` 不生效"报成缺陷 ——
   > 可前端编辑个人资料页**根本没有邮箱输入框**，需求里就没这个功能。
   > 同一把尺子还砍掉了"`phone` 可以重复"（文档只要求用户名/邮箱查重）。
   > 详见覆盖矩阵第六节的「判定纪律 / 观察点」。
10. **接口路径只准写在 `api/` 里，用例里不许出现 URL 字符串。**（2026-10-08 定）
   用例写 `api.user.get_profile(headers=auth_headers)`，**不写** `api.get("/user/profile", ...)`。
   理由就是"改一个接口要动几处"：收敛前光 `/user/profile` 一条路径在用例里出现 **17 次**、
   `/recipe/detail/{id}` 散在 **2 个文件**里 —— 后端哪天改路径，你得 grep 全局一处处改，
   **改漏一处就是一条莫名其妙的假红**；收敛后只需要改 `api/` 里的**一行**。
   - 新增接口 → 找对应的 `<模块>_api.py` 加一个方法（没有就新建一个）；
     方法名用**动作**命名（`get_profile` / `save_goal` / `search`），别写 `get` / `do`；
     把实测出来的坑写进 docstring（401 空体、非统一信封、upsert、哪些字段不可改…）。
   - **路径带变量**的接口（`/recipe/detail/{id}`）→ 变量做成参数：`detail(recipe_id)`。
   - **唯一例外**：故意打"不该存在的路径"的越权探针，走逃生舱 `api.raw_get()`，
     并在注释里写明为什么（见 `user/test_user_profile.py::test_no_id_based_profile_route`）。
     正常业务用例用它 = 把 URL 又写回了用例，这一层就白搭了。
   - ⚠️ 批量改写时**别只 grep `api.get("`** —— **f-string 动态路径**（`api.get(f"/x/{i}")`）
     会整个漏掉。本次重构就漏了 3 处，靠实跑才暴露。
     **注意**：当时 `Api` 不带 `get`，报错很扎眼（`AttributeError: 'Api' object has no attribute 'get'`）；
     现在 `Api` 继承了 `BaseApiClient`，**`api.get("/x")` 能跑通、不报错** ——
     也就是说这类漏网之鱼不会再自己炸给你看，只能靠"实跑 + 人工看用例"兜底。
11. **接口类都直接继承 `BaseApiClient`，不要再引入中间基类。**（2026-10-08 定）
   原来是两个类叠着用：`ApiClient`（负责发请求）+ `BaseApi`（负责存一个 client 给子类用），
   于是每个模块方法都得写 `self._c.get(...)` —— 想看懂要先理解两层继承。
   现在合并成一个：`class UserApi(BaseApiClient)` → 方法里直接 `self.get("/user/profile")`。
   - 新增模块类：`from .base_api_client import BaseApiClient`（同在 `api/` 包内，用相对导入），
     继承，用 `self.get/post/put/delete`。
   - ⚠️ 子类**自己写了 `__init__`** 时必须先 `super().__init__()`
     （`api/__init__.py` 的 `Api` 类就是例子）——子类一旦自己写了 `__init__`，
     Python 就不再自动用父类的，Session 不会被创建，一调就 `AttributeError`。
   - ⚠️ **代价要说清**：`Api` 现在也带着继承来的 `get/post`，所以 `api.user.post("/任意路径")`
     语法上能跑。防线从"结构上不给"变成了"约定上不用"——靠这条约定和 code review 守。

12. **Allure 只许"旁路"：报告挂掉不许把用例搞红；标签只在一个文件里维护。**（2026-10-21 定）
    - **新增测试文件 → 去 `common/allure_helper.py` 的 `STORY_LABELS` 补一行中文名。**
      漏了不会报错（有兜底：`test_recipe_search` → `recipe search`），只是报告里不好看。
    - **不许在用例里 `import allure` 自己贴东西。** 请求/响应、AI 问答已经在
      `api/base_api_client.py` 和 `common/logger.py` 埋好了，一处埋点全场覆盖；
      用例各贴各的，就会出现"有的用例有附件、有的没有"，报告的价值立刻塌一半。
    - **不许绕过 `common/allure_helper.py` 直接调 `allure.attach`。** 那个文件里做了
      **截断**（单段 2 万字符，SSE 和大响应体不作截断能把报告干到几百 MB）和
      **脱敏**（`Authorization` / `password`）——绕过去等于把凭据明文摊进一份会被转发的 HTML。
    - 加任何"报告层面"的东西之前先问一句：**它挂了会不会把绿的用例搞红？**
      会 → 包进 `_safe()`，或者干脆别做。**观测工具不该成为被测对象。**
    - ⚠️ **别在埋点里读不该读的东西**：对 `stream=True` 的响应调 `resp.text`
      会把整条流读干，`test_assistant_流式.py` 当场挂。判据是
      "贴给报告的内容，必须是本来就该读、且读一次没关系的东西"。

---

## 六、已知的"文档 vs 实现"不一致（缺陷候选）

练习过程中实测发现的，对应路线图"失败用例比成功用例值钱"：

| # | 现象 | 涉及接口 | 记录位置 | 状态 |
|:--:|:--|:--|:--|:--|
| 1 | 文档写"无需认证"，实测无 token → 401 | `GET /recipe/search` | `recipe/test_recipe_search.py` | 待修复 |
| 2 | 缺 `keyword` 参数时返回 Spring 默认 400，不走统一信封 | `GET /recipe/search` | `recipe/test_recipe_search.py` | 待修复 |
| 3 | ~~`height=0` 触发 BMI 除零，把 MyBatis/MySQL 异常栈原样回给客户端~~ | `POST /health/info` | `health/test_health_info.py` | ✅ 已修复 2026-09-20 |
| 4 | ~~数值范围无校验：`age=-1`、`age=999`、`weight=-5`、`bloodSugar=-1` 都能保存~~ | `POST /health/info` | `health/test_health_info.py` | ✅ 已修复 2026-09-20 |
| 5 | ~~允许结束日期早于开始日期~~ | `POST /health/goal` | `health/test_health_goal.py` | ✅ 已修复 2026-09-20 |
| 6 | ~~upsert 更新数据后 `updateTime` 不刷新~~ | `POST /health/info` | `health/test_health_info.py` | ✅ 已修复 2026-09-20 |
| 7 | 非法日期格式返回的 400 不走统一信封 | `POST /health/goal` | 待补用例 | 待修复 |
| 8 | ~~`gender` 无白名单，库里 `male`/`female`/`男` 三套取值并存；且落库的字面值直接决定 BMR 走哪个公式，写错不报错只算错~~ | `POST /health/info` | 待补用例（`gender_whitelist_check.py` 临时脚本验证） | ✅ 已修复 2026-09-20 |
| 9 | `PUT /user/profile` 更新后 `updateTime` **不刷新**（停在注册时间不动）—— **与 #6 同源**，同一个 `updateById` 毛病在另一个接口原样复现 | `PUT /user/profile` | `user/test_user_profile.py`（**xfail 固化**） | 待修复 |
| 10 | 越权被拒时返回 403 + Spring 默认错误体（`{timestamp,status,error,path}`），**不走统一信封** | 全部管理员接口 | `user/test_user_profile.py` | 待修复 |
| 11 | ~~`PUT /user/profile` 改手机号**不查重**，可以把号改成别人正在用的（`POST /auth/register` 同样没查）；表上 `phone` 也无唯一索引——而同一方法里 `username` 是有查重的~~ | `PUT /user/profile`、`POST /auth/register` | `user/test_user_profile.py` | ✅ 已修复 2026-09-30 |

> 完整版（含影响分析、优先级）见 `docs/接口覆盖矩阵.md` 第六节。

### 已修复的 6 条（#3 / #4 / #5 / #6 / #8 / #11）分别改了什么

**#5 日期倒挂** —— `DietGoalDTO` 加 `@AssertTrue` 跨字段校验方法 `isDateRangeValid()`。
规则同时依赖两个字段，单字段注解表达不了，所以挂在 getter 上做类级校验；
两个日期任一为空放行（`endDate` 本就可选），只拦真正的倒挂。

**#3 和 #4 其实是同一个病根**：参数层面完全没有范围校验。在 `HealthInfoDTO` 上补：

- `height`：`@DecimalMin("50") / @DecimalMax("250")` —— 顺带堵死了 `height=0`
  算出 `Infinity`、再炸出 MyBatis 异常栈并原样返回的那条路。
- `age`：`@Min(1) / @Max(150)`；`weight`：`@DecimalMin("10") / @DecimalMax("500")`；
  `bloodSugar`：`@DecimalMin(value="0", inclusive=false) / @DecimalMax("50")`。

三个容易踩的点：
① **Double 字段必须用 `@DecimalMin/@DecimalMax`** —— `@Min/@Max` 只支持整数系类型
（byte/short/int/long + 包装类、BigInteger/BigDecimal），挂在 `Double` 上会抛 `UnexpectedTypeException`；
② 同一字段的上下限**共用一条 message**，否则调用方收到哪句取决于校验器的执行顺序，不可控；
③ **定范围前先核对库里存量数据**（这次含 120 条模拟用户），确保已有记录不会变成"非法"——
否则那些用户下次改档案会被新规则拦死。

**#6 updateTime 不刷新** —— 根因很反直觉：表定义里 `update_time` **本来就是
`ON UPDATE CURRENT_TIMESTAMP`**，本该自动更新；但 MyBatis-Plus 的 `updateById`
默认策略是"非 null 字段一律写进 SET"，而实体是从库里查出来的、`updateTime` 带着旧值，
于是 SQL 变成了 `update_time = <旧值>`，**显式赋值把数据库的自动刷新盖掉了**。
修法：`updateById` 之前显式 `setUpdateTime(LocalDateTime.now())`。

> ⚠️ **2026-09-30 补记：这个病还在，只是换了个接口。**
> 实测 `PUT /user/profile` 更新后 `updateTime` 同样停在**注册时刻**不动
> （注册 16:17:36 → 两次 PUT 在 16:17:39 / 16:17:42 → API 与 DB 都仍是 16:17:36）。
> 说明 `updateById` 这个坑**不是 health 独有的**，凡是走 MyBatis-Plus 全量写回的更新接口都得查一遍。
> 已记为本表 **#9**，并用 `user/test_user_profile.py::test_update_time_refreshed_on_profile_write`
> 挂 `xfail` 固化 —— 后端修好后它会自己变 XPASS。

**回归结果**：`health/test_health_info.py` + `health/test_health_goal.py` 里对应的 4 条断言全部由 XFAIL 转为
**XPASS**（独立跑时）；另用临时脚本验证了 21 个边界场景 + updateTime 刷新，全部符合预期、数据已还原。

**2026-09-29 收尾**：这 4 条已**摘掉 `@pytest.mark.xfail` 标记，转为正式守卫用例**
（函数名也从 `test_bug_xxx` 改成描述契约的名字，如 `test_negative_age_rejected`）。
这正是 xfail 的用法闭环 —— 它变 XPASS 就是在提醒你"可以摘了"；摘掉之后哪天再退化，会**直接变红**。

> ⚠️ 摘标记时顺手抓到一个**测试自己的 bug**，值得单独记住：
> `test_update_time_refreshed_on_write` 原来写的是 `assert after != before`（"变了没变"），
> **单跑能过、跟 health 其他用例一起跑必红** —— 因为前一条用例的 teardown 刚 POST 过，
> 两次写入落在**同一秒**，而 `updateTime` 精度只到秒（实测：相隔 0.2 秒的两次写入返回同一个值）。
> 这叫**顺序依赖的假失败**：测试挂了但产品没毛病。
> 正确写法是判"是否接近当前时刻"（`abs(now - after) <= 300s`），既不受秒精度影响，
> 也照样能抓到原来的 bug（旧值停在几个月前）。改完连跑 3 次稳定 18 passed。

**#8 gender 取值归一** —— 这条不是"多写了个校验"，而是**消除一个静默的计算错误**。

归一前的乱象：库里 `male` 83 / `female` 98 / `男` 3 **三套取值并存**；
而 BMR 公式的分支写成了三处**标准不一致**的判断——

- `HealthInfoEdit.vue`：`gender === '男'`（**最窄，只认「男」**）
- `dietGoalRecommendation.js`：`=== '男' || === 'male'`（不忽略大小写）
- 后端 `HealthInfoServiceImpl.calculateBMR`：`"male".equalsIgnoreCase(...)`（忽略大小写）

后果：一个 `male` 用户打开编辑页保存，`isMale` 为 `false` → **按女式公式重算 BMR**
（测试账号正确值 1703 会被写成 1515，差 12%）→ POST 回库。**全程不报错**，
因为 `required` 只看非空，`'male'` 是非空串。

归一方案定 **`male` / `female`（英文小写）**，而不是统一成中文，理由：

1. **迁移量**：库里已有 181 条英文值，只有 **3 条**中文要改（反向要改 181 条）；
2. **后端本意**：`calculateBMR` 早就写成 `equalsIgnoreCase("male")`，DB 注释里的「男/女」才是残留；
3. **前端零感知**：只改 radio 的 `value`，标签文字仍是「男」「女」。

改动共 5 处（**顺序不能颠倒**）：

1. **DB**：`UPDATE health_info SET gender='male' WHERE gender='男'`（3 行，实测 `male 86 / female 98`）；
2. `HealthInfoBasic.vue` / `HealthInfoEdit.vue` 的 radio：`value="男"` → `value="male"`；
3. `HealthInfoEdit.vue` 的 `isMale` 判定：`=== '男'` → 改用公共工具（**这处漏了等于白改**）；
4. `dietGoalRecommendation.js`：同样收拢到公共工具；
5. 后端 `HealthInfoDTO`：加 `@Pattern(regexp = "male|female", message = "性别取值不合法，只能是 male 或 female")`。

新建了 `frontend/src/utils/healthEnums.js` 收拢字典与判定，避免 `'male'` 硬编码散在四处。
新增一个**显示映射** `genderLabel()`：库里存英文、界面显示中文——这条最容易漏，
不补的话「我的健康档案」页会直接把 `male` 显示给用户。

**两条必须记住的坑**：

① **`el-radio` 的 `value` 是发到后端的数据，标签文字只是给用户看的。**
"前端传男女"这个说法本身就不成立——用户点的是「男」，发出去的是 `value`。
所以"让前端统一发英文"**不需要写任何转换代码**，改 `value` 就行。

② **白名单必须最后加。** 先加 `@Pattern` 再迁数据，那 3 条存量 `男` 会被自己的记录拦死
（用户下次改档案直接 400，而且不知道怎么改）。

**回归结果**：临时脚本 12 个场景全过（`male`/`female` → 200；`男`/`女`/`MALE`/`Male`/`'男 '`/`'male '`/`X` → 400 统一信封；
`''`/缺字段/`null` → 400「性别不能为空」），数据已还原（14 个字段一致）；
全套 `106 passed + 4 xpassed` 无回归。

> 顺带说明：`@NotBlank` 与 `@Pattern` 同时挂在 `gender` 上**不冲突**——
> 字段缺失（null）时 `@NotBlank` 报「性别不能为空」，`@Pattern` 对 null 放行（Bean Validation 规范行为）；
> 空串 `''` 两个都会失败，实测报的是「性别不能为空」，与既有用例 `test_info_required_fields[缺gender]` 一致。

**#11 手机号无唯一校验** —— 一个"漏了一层"的典型：同一个方法里 `username` 有查重，`phone` 什么都没有。

实测：把自己的 `phone` 改成**别人正在用**的号 → **HTTP 200，真的写进库**；
而同一接口把 `username` 改成别人的 → 400「用户名已存在」。表结构也印证：
`username` / `email` 都有 UNIQUE 索引，**`phone` 一个索引都没有**。

修了三层，**层层都不能省**：

1. **Service 查重**（`UserServiceImpl` 的 `updateProfile` + `register`）：仿照已有的 username 查重写法。
   要点：判断条件必须**排除自己**（`!phoneOwner.getId().equals(userId)`），
   否则"提交自己的原号"会被自己拦死。注册接口同样漏了，一起补上。
2. **数据库唯一索引** `uk_phone`：Java 的"先查后写"**挡不住并发**——
   两个请求同时查、都查不到、都去写，谁也没错。唯一索引才是最终防线。
   实测直连 SQL 写重复号被拦：`(1062, "Duplicate entry '17840529449' for key 'user.uk_phone'")`。
   ⚠️ **建索引前先清了存量重复**：`19330406783` 被 id=2 和 id=100181 **两个账号共用**（种子数据自带的），
   给 id=100181 换成 `13800138001` 才建得上 —— 又是"先看存量、再定规则"那条教训。
3. **顺手修掉"写了删不掉"**：`avatar` 传空串现在能真正存成 `NULL` 了。
   根因是 MyBatis-Plus `updateById` 的默认策略 `NOT_NULL` **会跳过 null 字段**——
   Service 里写 `setAvatar(null)`，内存里改了、SQL 里根本没有这一列、库里纹丝不动。
   修法：`User.avatar` 加 `@TableField(updateStrategy = FieldStrategy.IGNORED)`。

**契约澄清（改完要记住的三句话）**：

- `null` = "这个字段不改"（三个字段一致）；
- `""` 在 `phone` 上 → **400「手机号格式不正确」**，即**手机号不可解绑**（`avatar` 相反，空串 = 清空）；
- 撞车 → 400「手机号已被使用」。

> 为什么要专门澄清：修的过程中一度把 `""` 放开成"解绑"，结果和
> `test_user_profile.py::test_update_phone_invalid_format_rejected[空串]` 直接撞车
> —— 那条用例断言"空串应被拒"。**`""` 不能既是"非法输入"又是"解绑指令"**，
> 最后按用例的契约回退成 400。这也说明：**写用例就是在定契约**，改行为前先看一眼有没有用例守着。

**回归结果**：临时脚本 17 个场景全 PASS（含"改他人号被拒且库里没动"、"提交原号幂等放行"、
"注册占用他人号被拒"、"SQL 直写重复号被唯一索引拦住"），数据已还原
（`username`/`phone`/`avatar`/两个时间戳逐一比对一致）；全套 `150 passed + 1 xfailed`，无回归。

---

### ⚠️ 遗留的测试侧问题：`test_bug_update_time_not_refreshed` 会因为"撞秒"假失败

这条用例写的是 `assert after != before`，但 `updateTime` 的精度是**秒**。
文件级/全套连续跑时，**前一条用例的 teardown 还原**与本用例的写入会落在**同一秒**，
`after == before` 于是变成假失败（记为 XFAIL）——后端其实是好的。

实测：单独跑这条 6/6 通过；整个文件连着跑 4/4 失败。这就是"测试用例之间的时间耦合"。

**修法**：别比"变了没有"（同秒分不出），改比"是否刷新成了当前时间"：

```python
from datetime import datetime, timedelta

def test_update_time_refreshed_on_update(api, auth_headers, info_env):
    """写入后 updateTime 应刷新为"写入那一刻"。

    注意别写 assert after != before：updateTime 精度到秒，
    只要前一条用例的还原和本次写入落在同一秒，就会假失败。
    改判"它是否贴近当前时间"——没刷新时它会是一个很久以前的值，必然被这条断言抓住。
    """
    info = info_env
    api.assert_ok(api.post("/health/info", json={**info, "age": (info["age"] or 0) + 1},
                           headers=auth_headers))
    after = datetime.fromisoformat(
        api.assert_ok(api.get("/health/info", headers=auth_headers))["data"]["updateTime"])
    assert datetime.now() - after < timedelta(seconds=10), \
        f"写入后 updateTime 应刷新为当前时间，实际是 {after}（距现在超过 10 秒 → 没刷新）"
```
