# Allure 报告 · 使用与实现说明

> 一句话：**跑用例的过程照旧在控制台看，跑完的结果进 Allure 网页看。**
> 控制台解决"现在在跑哪条、红没红"，Allure 解决"这条为什么红、请求发了什么、回了什么、
> 哪个模块最脆、跟上一轮比是变好了还是变差了"。

---

## 一、报告里到底有什么（先看这个，再决定要不要读后面）

打开报告后，左边栏是六个视图，各自回答一个问题：

| 视图 | 回答什么问题 | 数据从哪来 |
|:--|:--|:--|
| **Overview** | 这轮总共多少条、红了几条、哪种红最多 | 全部用例结果 |
| **Categories** | **红的那些，是"后端挂了"还是"接口行为不对"还是"我们自己写错了"** | `config/allure_categories.json` |
| **Suites** | 按"接口自动化 → 模块 → 文件"的树形结构看 | conftest 自动打的 `suite/subSuite` 标签 |
| **Behaviors** | 按"业务功能"看（不看目录结构） | conftest 自动打的 `epic/feature/story` 标签 |
| **Graphs** | 状态饼图、严重级别分布、**趋势图（跟前几轮比）** | 让 severity 有用的地方 |
| **Timeline** | 哪些用例是并行/串行的、谁最慢 | 每条用例的起止时间 |

**单条用例详情页**才是真正省时间的地方，一屏能看到：

- **Parameters** —— 参数化用例的这组入参（`{name: 密码错误, email: ..., want_code: 400}`），
  不用再去翻 YAML 是第几行；
- **Attachments** —— 这次用例里**每一次 HTTP 交互**的完整请求 + 响应（见第三节）；
- **log** —— pytest 捕获的日志（我们 `log.info` 打的那些）；
- **Trace** —— 失败时的完整断言栈；
- **Severity / Epic / Feature / Story** —— 这条用例的定位标签；
- **Duration** —— setup / call / teardown 各花了多久（夹具里登录慢，一眼就看得出来）。

---

## 二、第一次用要准备什么

只有两件事，都只需要做一次。

### 1) 装 Python 依赖

```bash
cd D:\jiankang\healthy\automation_api_requests_pytest
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`allure-pytest` 是新增的那一个。它只负责**产出原始结果**
（`reports/allure-results/*.json`），**不负责渲染网页** —— 渲染是下一件事。

### 2) 准备 Allure 命令行工具（一次性，约 29 MB）

渲染网页靠的是 Allure 官方的 **Java** 命令行工具（`allure-commandline`），
它不是 pip 包，要单独下。本项目已经把它放在：

```
tools/allure-cli/allure-2.46.1/     ← 已在 .gitignore 里，不进仓库
```

换台机器/重新 clone 时，重新下一次就行（任选一种）：

```powershell
# 方式 A：直接下 zip 解压到 tools/allure-cli/（和现有布局一致）
#   下载页：https://github.com/allure-framework/allure2/releases
#   Maven 中央库直链（本机实测可用）：
#   https://repo1.maven.org/maven2/io/qameta/allure/allure-commandline/2.46.1/allure-commandline-2.46.1.zip

# 方式 B：用 npm
npm i -g allure-commandline

# 方式 C：已经有别处的 allure，设个环境变量指过去
$env:ALLURE_CLI = "D:\tools\allure\bin\allure.bat"
```

还要求 **JRE 17+**（本机是 JDK 21，`JAVA_HOME` 已配好）。
`tools/allure_report.py` 会自己检查这两样，缺了会直接告诉你缺哪个、去哪补。

> 验证一下齐了没：
> ```bash
> .venv\Scripts\python.exe tools\allure_report.py --clean
> ```
> 打印出 `allure : ...` 和 `java : ...` 两行就是齐了。

---

## 三、怎么跑

### 最常用：两步

```bash
# 第 1 步：跑用例（和以前一模一样，只是顺带产出了 allure 结果）
.venv\Scripts\python.exe -m pytest test_cases -q

# 第 2 步：把结果渲染成网页
.venv\Scripts\python.exe tools\allure_report.py --open
```

`--open` 会起一个本地小服务（默认 `http://127.0.0.1:4040`）并自动打开浏览器。
**不能直接双击 `index.html`** —— 报告是纯前端 + 一堆 JSON，`file://` 下读本地 JSON
会被浏览器拦掉，页面会一片空白。

### 一条命令搞定（推荐给"跑一遍看看"的场景）

```bash
# 跑全套 → 清空上轮结果 → 出报告 → 打开
.venv\Scripts\python.exe tools\allure_report.py --run --open

# 只跑某个模块（后面的参数原样透给 pytest）
.venv\Scripts\python.exe tools\allure_report.py --run test_cases/auth -q --open
.venv\Scripts\python.exe tools\allure_report.py --run test_cases/health -k 目标 --open

# 只跑"严重级别 = critical"的（登录 / 用户资料 —— 挂了说明鉴权和越权出问题）
.venv\Scripts\python.exe -m pytest test_cases --allure-severities=critical -q
.venv\Scripts\python.exe tools\allure_report.py --open

# 只跑某个业务功能（标签是自动打的，不用去改用例）
.venv\Scripts\python.exe -m pytest test_cases --allure-features="AI 助手" -q
```

### 全部参数

| 参数 | 作用 |
|:--|:--|
| `--run [目标]` | 先跑 pytest 再出报告；不写目标 = `test_cases` 全套；**跑前会清空旧结果** |
| `--open` | 生成后起服务并打开浏览器 |
| `--serve` | **不生成静态文件**，直接起服务看原始结果（调试用，关掉就没了） |
| `--clean` | 只清空结果目录 |
| `--fresh` | 生成时连历史一起清掉（趋势图归零） |
| `--results DIR` | 换结果目录（默认 `reports/allure-results`） |
| `--report DIR` | 换报告输出目录（默认 `reports/allure-report`） |
| `--port N` | `--open` / `--serve` 的端口（默认 4040） |
| `--allure PATH` | 手动指定 allure 命令行工具 |
| 其它未知参数 | 原样透给 pytest（配合 `--run`） |

> **产物会不会污染仓库？** 不会。`reports/` 与 `tools/allure-cli/` 都在 `.gitignore` 里。
> 报告是**纯静态页面**（`reports/allure-report/` 整个目录），可以直接打包给同事、
> 丢到 nginx 上，对方不需要装 Python / Java。

---

## 四、这套集成做了什么（六个设计决定）

### 决定 1：结果目录写在 `conftest.py` 里，**不写进 `pytest.ini`**

`pytest.ini` 的 `addopts` 里写 `--alluredir=reports/allure-results` 看起来最直观，
但实测有两个坑：

1. **相对路径按"当前工作目录"解析**。PyCharm 里把工作目录设成 `test_cases/` 时，
   结果会写到 `test_cases/reports/` 下面 —— 找不到，还以为是"报告没生成"。
2. **没装 `allure-pytest` 的机器会直接崩**：pytest 把 `--alluredir` 当成
   未知参数，报 `unrecognized arguments`，**290 条用例一条都跑不起来**。
   一个可选的报告不该有这种杀伤力。

所以改成：`conftest.py::pytest_configure`（挂了 `tryfirst`）里按 `rootdir`
算出**绝对路径**再塞回 `config.option.allure_report_dir`，allure 自己的
`pytest_configure` 随后读到的就是它。没装 allure 时整段自动跳过，
用例照跑、日志照打，只是不出报告。

> 代价：`pytest.ini` 里看不到这行配置，得靠 conftest 里的注释指路。
> 好处是"装不装都能跑"，这一条更值钱。
>
> 想临时换个目录：`pytest test_cases --alluredir=D:\tmp\results` —— 传了就听你的，
> 而且**不会**替你清空（自己指定的目录，攒历史是你的自由）。

### 决定 2：层级标签**按 nodeid 自动推**，不给用例加装饰器

`epic / feature / story / suite / subSuite / severity` 七个标签，
全部由 `common/allure_helper.py::derive_labels()` 从路径推出来：

```
test_cases/auth/test_login.py::test_login[密码错误]
   ↓
epic        = 健康饮食后端 · 接口自动化
parentSuite = 健康饮食后端 API
suite       = 登录注册            ← 目录名（auth）
subSuite    = 登录                ← 文件名
feature     = 登录注册
story       = 登录
severity    = critical            ← 目录 → 级别（auth/user = critical）
```

为什么不给 290 条用例逐个加 `@allure.feature("登录")`：

- **加新用例时一定会忘**。忘了不会报错，只会掉进报告里变成一个没分类的孤儿，
  而且要等有人翻报告才发现；
- 换个分组口径（比如"AI 助手"要不要再拆成"安全"和"功能"）要动几十个文件。

项目本来就有"目录 = 模块、文件 = 资源"的约定（README 第五节第 6 条），
标签直接从这套约定里长出来，**零维护**。要改名只改一张表
（`allure_helper.py` 的 `STORY_LABELS` / `MODULE_LABELS`）。

单条用例想标得更细，直接加装饰器，**用例自己写的优先**（conftest 会跳过已有类型）：

```python
import allure

@allure.severity(allure.severity_level.BLOCKER)
@allure.title("越权删除别人的会话必须失败")
def test_delete_other_users_conversation(...):
    ...
```

### 决定 3：每次 HTTP 请求自动贴「请求 + 响应」两个附件

埋点只有一个地方 —— `api/base_api_client.py::_log()`。项目里所有业务请求都走它，
所以**一处埋点、全场覆盖**，290 条用例一行都不用改。

拆成两个附件而不是拼成一大段：报告里附件是独立面板，请求和响应并排才能对账
（"我传了这个，它回了我那个"）。

失败用例同样有这两个附件 —— 这才是它最值钱的时候。红了一条，
点进去先看响应体里的 `message`，比翻 `logs/runs/` 快得多。

### 决定 4：报告里的凭据**默认脱敏**

报告是会被转发出去的东西（贴群、发邮件、丢 nginx），所以：

- 请求头里的 `Authorization` → `Bearer eyJhbGci…***（已脱敏）（共 172 字符）`
  （**故意留前 8 个字符**：越权用例靠"这是谁的 token"回看现场，全打码就看不出是谁了）；
- 正文里 `password` / `token` / `accessToken` / `refreshToken` 的值 → `***（已脱敏）`。

本地排查要看明文：`$env:ALLURE_NO_MASK=1`。

### 决定 5：SSE 流式响应**不读 body**

`test_assistant_流式.py` 用的是 `stream=True`。对这类响应调 `resp.text`
会把整条流读干，**接口层随后就拿不到数据，用例直接挂**。
所以 `attach_http` 见到 `Content-Type: text/event-stream` 只贴响应头，
正文由接口层自己解析完再决定怎么记。

> 这类"观测动作反过来影响被测对象"的坑，是所有埋点里最容易踩的一种。
> 记住判据：**贴给报告的东西，必须是本来就该读、且读一次没关系的东西。**

### 决定 6：报告出错**永远不许把用例搞红**

`allure_helper._safe()` 把所有上报异常吞掉（`ALLURE_DEBUG=1` 时才抛）。
理由：报告是旁路。磁盘满、allure 内部状态异常、在用例之外被调用 ——
正确的表现是"这条附件没有"，而不是让一条本来通过的用例变红。
**把观测工具变成被测对象**，是自动化里最亏的一种失败。

### 另外两件小事

- **`log_qa()` 会把 AI 问答全文贴进报告**。AI 用例的断言往往只是"没出现某个词"，
  绿灯但答非所问只有把原文摊出来才看得见。控制台仍然只打一行（要能扫），
  报告里是全文（要能复盘）。
- **`environment.properties` / `categories.json` 在会话收尾写入**。
  前者回答"这份报告是在哪台机器、打哪个后端、什么版本下跑的"；
  后者是缺陷分类规则（见下）。

---

## 五、缺陷分类：Categories 视图

`config/allure_categories.json` 里的规则，按顺序**先匹配先算**：

| 分类 | 匹配条件 | 意思 |
|:--|:--|:--|
| 环境问题：后端 / 数据库没起 | broken/failed + 连接超时、拒绝连接、代理错 | **不是代码问题，别去改用例** |
| 已知缺陷已修复（XPASS） | failed + 消息带 `XPASS` | 后端修好了 → **去把 xfail 标记摘掉** |
| 断言不符：接口行为与预期不一致 | failed + `AssertionError` | 真问题：要么后端改了行为，要么需求变了 |
| 已知缺陷（xfail 固化，等后端修） | skipped + 消息带 `XFAIL` | 早就知道的坑，不算回归 |
| 用例 / 夹具自身出错 | broken（兜底） | 我们的测试代码写错了 |

这张表的价值在于**把"三种红"拆开**：

- 后端没起 → 一堆红，但一条都不用修，去看服务；
- xfail 变 XPASS → 一条"红"其实是好消息，提醒摘标记；
- 真的断言不符 → 这才是要干活的。

全堆在一个"失败"数字里，就只能一条条点开看，还得自己判断。

---

## 六、怎么验证"报告本身"是对的

业务用例全绿的时候，看不出报告有没有问题（附件贴没贴、分类生效没）。
`tools/allure_selftest/test_allure_check.py` 是**故意做红**的一组自检用例：

```bash
# 用独立的结果目录，别污染正式报告
.venv\Scripts\python.exe -m pytest tools/allure_selftest -q `
    --alluredir=tools/allure_selftest/_results --clean-alluredir

.venv\Scripts\python.exe tools\allure_report.py `
    --results tools/allure_selftest/_results --report tools/allure_selftest/_report --open
```

报告里应该能看到：

- 2 条通过、1 条断言失败、1 条 broken、1 条 xfail（skipped）；
- **Categories 里正好三类**：断言不符 / 环境问题 / 已知缺陷；
- 通过的那条点进去，Attachments 里有两个附件（请求、响应）；
- 失败的断言里能看到 `- 这条是故意写错的期望值 / + 登录成功` 这种 diff；
- Overview 右侧"环境"面板有 15 项，`ALLURE_PYTEST` 有版本号、`PYTEST` 对得上。

> 产物目录取名 `_results` / `_report`，是为了蹭 `.gitignore` 里的 `_*` 规则（不进仓库）。
> 自检用例本身**不会被 `pytest` 自动跑到** —— `pytest.ini` 的 `testpaths = test_cases`
> 把范围限死了，只有显式 `pytest tools/allure_selftest` 才会执行。
> 验证完可以直接删掉两个产物目录。

---

## 七、常见问题

**Q：浏览器打开是一片空白 / 一直在转圈。**
用 `file://` 直接开的 `index.html`。必须走 http 服务：
`python tools/allure_report.py --open`。报告数据是 JSON，`file://` 下读不到。

**Q：报告顶部"环境"面板里中文变乱码。**
`environment.properties` 是 Java 程序读的，按 ISO-8859-1 解码，
中文必须写成 `\uXXXX` 转义。`allure_helper._properties_escape()` 已经做了，
别手动往那个文件里写中文。

**Q：`--open` 报端口被占用。**
换端口：`--port 4041`。

**Q：生成出来是空报告 / 提示"结果目录里没有结果"。**
还没跑用例。先 `python -m pytest test_cases`，或者直接用 `--run`。

**Q：报告越来越大 / 想从头来过。**
`--fresh` 会连历史一起清（趋势图归零）。`reports/` 下的旧报告还可以用
`python tools/clean_artifacts.py` 按天清理。

**Q：一次跑 290 条，报告几百 MB、浏览器卡。**
先按模块跑（`--run test_cases/auth`），或按标签筛选
（`--allure-severities=critical`）。正文附件已经限制在单段 2 万字符以内。

**Q：`allure` 命令找不到。**
它默认不在 PATH 里。三种解法（按优先级）：
`--allure <path>` → `$env:ALLURE_CLI` → 解压到 `tools/allure-cli/`。
脚本每次都会打印它实际用的是哪个。

**Q：能不能在 CI 上跑？**
可以，而且这才是它的主场景。CI 里通常是：
`pytest ... --alluredir=allure-results` → `allure generate allure-results -o allure-report`
→ 把 `allure-report/` 当构建产物发出去。本脚本的 `--run` 就是这套流程的本地版。
**别在 CI 上用 `--open`**（会起一个前台服务，构建卡住）。

**Q：它和 `logs/runs/*.log` 重复吗？**
不重复，两者回答不同问题：
日志是**线性流水**（"跑的时候发生了什么"），适合 `grep`、适合追一条链路；
报告是**按用例组织的结构化结果**（"哪些红了、为什么、入参是什么"），
适合看整体、给别人看。日志里有的报告里不一定有（例如每次 SQL 的耗时），
报告里有的日志里很难找（例如"这 12 条红都是一个原因"）。

---

## 八、涉及的文件

| 文件 | 作用 |
|:--|:--|
| `common/allure_helper.py` | **唯一的 allure 出口**：附件、脱敏、标签推导、环境信息。没装 allure 时静默降级 |
| `conftest.py` | `pytest_configure` 定结果目录；`pytest_collection_modifyitems` 打标签；`sessionfinish` 写环境/分类 |
| `api/base_api_client.py` | `_log()` 里一行 `attach_http(resp)` —— 一处埋点覆盖全部业务请求 |
| `common/logger.py` | `log_qa()` 贴问答全文；`log_response()` 贴完整响应 |
| `config/allure_categories.json` | 缺陷分类规则（五类，先匹配先算） |
| `tools/allure_report.py` | 找工具链 → 跑用例 → 生成 → 打开 |
| `tools/allure_selftest/` | 故意做红的自检用例（`testpaths` 限死，不会被自动跑到） |
| `reports/allure-results/` | 原始结果（每次运行的 JSON，会被清空） |
| `reports/allure-report/` | 生成的静态网页（可直接拷走） |

---

## 九、两个容易"用了才发现"的细节

**① 趋势图（Trends）要跑第二轮才有第二根柱子。**
allure 2.46 的 `generate` 见到目标目录已存在会直接拒绝，所以必须带 `--clean`；
但 `--clean` 又会连旧报告里的 `history/` 一起删掉。两头一夹，趋势就永远只有本轮。
`tools/allure_report.py` 因此在生成前多做一步：**把旧报告里的 `history/`
复制进结果目录**，allure 据此算出"跟前几轮比"，再产出新的 `history/`。
想归零就用 `--fresh`（跳过这一步）。

**② 本轮"没有红"，Categories 视图会是空的。**
分类只作用在失败/跳过/崩溃的用例上；全绿时它没有东西可装，
这是正常现象（自检用例就是专门造红来验它的）。

