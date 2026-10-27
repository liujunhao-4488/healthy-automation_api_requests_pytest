# 健康饮食推荐系统

一个可本地运行、可进 CI 的全栈健康饮食项目：

**Vue 3 前端 + Spring Boot 后端 + Flask 算法服务 + MySQL**，覆盖食谱推荐、健康档案、饮食记录、AI 助手（RAG）、健康文章与后台管理；配套 **346 条**接口自动化用例。

---

## 一、系统架构

```
┌──────────────────────────┐
│  Web 前端      :5173     │  Vue 3 + Element Plus + ECharts
│  新版前端      :5174     │  Vue 3 + Vite 5（front2）
│  移动端                 │  uni-app（app/）
└────────────┬─────────────┘
             │  /api
             ▼
┌──────────────────────────┐        ┌─────────────────────┐
│  后端 Spring Boot :8080  │───────▶│  MySQL :3306         │
│  /api                    │        │  health_diet         │
│  JWT / 业务 / 数据组装    │        │  health_diet_test    │
└────────────┬─────────────┘        └─────────────────────┘
             │  推荐 / RAG 检索
             ▼
┌──────────────────────────┐        ┌─────────────────────┐
│  算法服务 Flask :5000     │───────▶│  权威文件 / 站内文章  │
│  推荐引擎 + 知识库检索     │        │  （RAG 语料）        │
└──────────────────────────┘        └─────────────────────┘
             ▲
             │  接口自动化（346 条）
┌────────────┴─────────────┐
│  automation_api_requests │  pytest + requests + Allure
│  _pytest                 │  依赖 MySQL / 8080 / 5000
└──────────────────────────┘
```

三个外部依赖缺一个，自动化测试会**环境预检直接中止**，不会跑出一片红。

---

## 二、目录结构

| 目录 / 文件 | 作用 |
| --- | --- |
| `frontend/` | Web 前端（Vue 3 + Element Plus + ECharts + Pinia），端口 5173 |
| `front2/` | 另一版 Web 前端（Vue 3 + Vite 5），端口 5174 |
| `app/` | uni-app 移动端（“智能饮食推荐”），用 HBuilderX 运行 |
| `backend/` | Spring Boot 2.7 / Java 21 + MyBatis-Plus + Spring Security(JWT)，端口 8080，前缀 `/api` |
| `algorithm/` | Flask 算法服务：食谱推荐 + RAG 知识库检索，端口 5000 |
| `database/` | 开发库全量 dump、测试库表结构 / 种子 / 一键重建脚本 |
| `automation_api_requests_pytest/` | 接口自动化：346 条 pytest 用例、接口封装、契约、Allure、评测工具 |
| `docs/` | 需求文档、AI 测试路线图 |
| `权威文件/` | RAG 权威语料（指南 PDF 等） |
| `API.md` | 后端接口文档（控制器方法级 78 个接口） |

---

## 三、功能模块

| 模块 | 能力 | 主要后端接口 |
| --- | --- | --- |
| 认证 | 注册、登录、JWT 鉴权 | `/auth/login`、`/auth/register` |
| 个人资料 | 用户名 / 手机号 / 头像、字段白名单 | `/user/profile` |
| 健康档案 | 档案 upsert、BMI/BMR、顶层 `analysis`、历史快照 | `/health/info`、`/health/history` |
| 饮食目标 | 目标 upsert、按目标推荐 | `/health/goal` |
| 饮食记录 | 记录提交、列表、详情、趋势、建议 | `/record/*` |
| 食谱 | 列表、详情、搜索、收藏、自定义 | `/recipe/*` |
| 推荐 | 食谱推荐、食材替代、按目标 / 今日推荐 | `/recommend/*` |
| 食材 | 列表、分类、搜索、营养、替代 | `/ingredient/*` |
| AI 助手 | 多轮会话、SSE 流式、意图分类、安全拦截、RAG 引用 | `/assistant/*` |
| 健康文章 | 列表、搜索、点赞、收藏、评论 | `/article/*` |
| 通知 / 后台 | 通知、后台总览、内容管理 | `/notification/*`、`/admin/*` |

> 算法服务目前只暴露 4 个接口：`/api/recommend/recipes`、`/api/kb/search`、`/api/kb/reload`、`/api/kb/stats`。其余业务逻辑在后端完成，不要按旧文档去找 `/api/analyze/health` 之类的接口。

---

## 四、环境要求

| 依赖 | 版本 / 说明 |
| --- | --- |
| JDK | **21**（`backend/pom.xml` 的 `java.version`） |
| Node.js | 18+（Vite 4/5） |
| Python | 3.11（CI 使用）；本地 3.10+ 即可 |
| MySQL | 8.0，默认端口 3306 |
| 系统 | Windows 下提供 `.bat` 一键脚本；Linux/macOS 按下面的命令手动跑 |

---

## 五、快速开始

### 5.1 数据库

**开发库** `health_diet`：用 `database/health_diet.sql` 手工导入（全量数据，含示例账号）。

**测试库** `health_diet_test`：不要复制开发库，直接一键重建：

```bash
database\rebuild_test_db.bat
# 等价于：python database/init_test_db.py --db health_diet_test
```

脚本会：

1. DROP / CREATE `health_diet_test`；
2. 导入 `schema.sql`（表结构）；
3. 导入 `seed_test.sql`：2 个测试账号 + 125 条食材 + **主账号 1 份健康档案 + 1 条历史**；
4. 打印 `user / ingredient / health_info / health_history` 数量；
5. 硬拒绝 `health_diet`，不会误删开发库。

> 跑自动化时后端必须连测试库：
> `set DB_NAME=health_diet_test`
> 连错库时环境预检会用 `userId + username` 对账并直接中止。

### 5.2 算法服务（Flask，5000）

```bash
cd algorithm
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

或直接双击 `algorithm/start_algorithm.bat`。

- 地址：`http://127.0.0.1:5000`
- 接口：
  - `POST /api/recommend/recipes` —— 食谱推荐（V2 引擎，失败自动退化到 V1）
  - `POST /api/kb/search` —— RAG 知识库检索
  - `POST /api/kb/reload` —— 重建索引（改了语料后不用重启）
  - `GET /api/kb/stats` —— 查看索引构成

> 索引是**懒加载**的：第一次访问 `/api/kb/stats` 或 `/api/kb/search` 时才构建。
> 改了 `权威文件/` 里的 PDF，先跑 `algorithm/ingest_authority.py`，再调 `/api/kb/reload`。
>
> ⚠️ 跑自动化时算法服务也要连测试库：`set DB_NAME=health_diet_test`
> （它从 `DB_USERNAME / DB_PASSWORD / DB_NAME` 读连接参数）。

### 5.3 后端（Spring Boot，8080）

```bash
cd backend
mvnw.cmd -DskipTests package
set DB_NAME=health_diet_test      # 跑自动化时；开发时用 health_diet
set DEEPSEEK_API_KEY=你的key       # AI 助手需要；没有会退化为本地回复
start-backend.bat
```

- 地址：`http://127.0.0.1:8080/api`
- `start-backend.bat` 会清掉宿主注入的 `SERVER__PORT`，并从 `HKCU\Environment` 读取 `DEEPSEEK_API_KEY`，避免环境变量不生效。
- 没有 `DEEPSEEK_API_KEY` 时，AI 助手仍能启动，但会返回固定错误文案（不调模型）；`p1` 那批依赖真实模型的用例会被 CI 排除。

### 5.4 前端（Vite，5173）

```bash
cd frontend
npm install
npm run dev
```

或双击 `frontend/start-frontend.bat`。

- 地址：`http://localhost:5173`
- Vite 已把 `/api` 代理到 `http://localhost:8080`，前端不需要单独配跨域。

`front2/` 是另一版前端（端口 5174）：

```bash
cd front2
npm install
npm run dev
```

移动端 `app/` 用 HBuilderX 打开运行。

### 5.5 启动顺序

```
MySQL(3306) → 算法服务(5000) → 后端(8080) → 前端(5173) → 自动化测试
```

---

## 六、接口自动化测试

目录：`automation_api_requests_pytest/`，详细说明见 [它的 README](automation_api_requests_pytest/README.md)。

### 6.1 规模

**346 条**（`pytest --collect-only` 实测）：

| 模块 | 条数 |
| --- | ---: |
| AI 助手（意图 / 安全 / 红队 / 流式 / 上下文 / RAG） | 221 |
| health（档案 / 目标 / 契约） | 45 |
| auth（登录 / 注册 / 登录契约） | 19 |
| user（资料 / 契约） | 19 |
| assistant 契约（响应形状） | 7 |
| 断言层自测（纯内存） | 28 |
| toolbox（数据加载器） | 7 |

已覆盖 **15 / 78** 个后端接口；`api/` 层封装 18 个方法（后端 15 + 算法服务 KB 3）。

### 6.2 跑之前

```bash
cd automation_api_requests_pytest

# 1) 重建测试库
..\database\rebuild_test_db.bat

# 2) 后端必须连测试库
set DB_NAME=health_diet_test

# 3) 确认 8080 / 5000 / 3306 都在
```

环境预检（MySQL → 后端 → 算法服务）缺一个就打印逐项 ✔/✘ 并中止，**不会产生几百条失败**。

### 6.3 常用命令

```bash
# 全量
.venv\Scripts\python.exe -m pytest -q

# 分层（收集阶段自动挂标记，用例文件不用改）
.venv\Scripts\python.exe -m pytest -m smoke -q        # 核心链路 118 条，不调模型
.venv\Scripts\python.exe -m pytest -m p0 -q           # 阻断级 149 条
.venv\Scripts\python.exe -m pytest -m p1 -q           # 模型依赖 197 条
.venv\Scripts\python.exe -m pytest -m regression -q   # 全量 346 条

# 并行（可选；AI 评测留痕必须串行）
.venv\Scripts\python.exe -m pytest -n 4 --dist=loadscope -q

# 只收集不执行（不需要服务）
.venv\Scripts\python.exe -m pytest --collect-only -q

# Allure 报告
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe tools/allure_report.py --open
```

### 6.4 已具备的能力

- 数据驱动：JSON / CSV / YAML / XLSX 四格式统一 `data_loader`；
- 统一断言：`assert_ok` + 可选 JSON Schema、`assert_error`；
- 响应契约：9 份 draft-07 schema + 4 个契约文件 + 28 条断言层自测；
- 会话 token 复用，401 自动重登一次；
- 网络类失败重试 2 次，单条用例超时 180 秒；
- 临时账号 / 会话清理登记表，会话收尾兜底硬删；
- Allure 请求响应附件、脱敏、按目录自动打标签；
- AI 评测留痕：`eval_record.py` → `tools/eval_results.json` → `tools/eval_runner.py`。

---

## 七、CI

工作流：[`.github/workflows/api-tests.yml`](.github/workflows/api-tests.yml)

GitHub Actions 会在 Ubuntu runner 上拉起整套系统：

```
MySQL 8.0（service 容器）→ 编译后端 → 启动 Flask → 启动后端 → pytest
```

| 触发 | 默认分层 |
| --- | --- |
| Pull Request | `smoke` |
| push `master` / `main` | `p0` |
| 每天定时 | `regression`（没配模型密钥时排除 `p1`） |
| 手动 `workflow_dispatch` | 自选 `smoke / p0 / p1 / regression` |

- Secret：`DEEPSEEK_API_KEY`。没配时 `p1` 会降级为 `smoke`，全量回归会排除 `p1`。
- 产物：Allure 结果、运行日志、`eval_results.json`、pytest 控制台日志。
- 工作流只在 GitHub 仓库上运行；推送到 Gitee 不会触发，需要推到 GitHub 或做镜像。

---

## 八、配置项

| 变量 | 作用 | 默认 |
| --- | --- | --- |
| `DB_HOST` / `DB_PORT` | 后端 / 算法服务连的 MySQL | `localhost` / `3306` |
| `DB_NAME` | 后端 / 算法服务使用的库 | `health_diet`（测试时改 `health_diet_test`） |
| `DB_USER` / `DB_PASSWORD` | 后端数据库账号 | `root` / `123456` |
| `DB_USERNAME` | 算法服务数据库账号（注意不是 `DB_USER`） | `root` |
| `DEEPSEEK_API_KEY` | AI 助手模型密钥 | 空（AI 助手返回固定错误文案） |
| `DEEPSEEK_BASE_URL` | 模型服务地址 | `https://api.deepseek.com` |
| `AUTOTEST_BASE_URL` | 自动化打的后端地址 | `http://127.0.0.1:8080/api` |
| `AUTOTEST_KB_BASE_URL` | 自动化打的算法服务地址 | `http://127.0.0.1:5000` |
| `AUTOTEST_DB_*` | 自动化直连测试库参数 | 与 `DB_*` 对应，库名 `health_diet_test` |
| `AUTOTEST_REQUIRE_DB` | `0` 时跳过直接访问 MySQL 的用例 | `1` |

> 后端 `start-backend.bat` 会主动清空 `SERVER__PORT`，避免被宿主环境覆盖端口。

---

## 九、文档索引

| 文档 | 内容 |
| --- | --- |
| [API.md](API.md) | 后端 78 个接口的请求 / 响应 / 错误码 |
| [automation README](automation_api_requests_pytest/README.md) | 自动化项目的目录、约定、跑法、知识点地图 |
| [接口覆盖矩阵](automation_api_requests_pytest/docs/接口覆盖矩阵.md) | 15 / 78 的逐接口覆盖状态与优先级 |
| [接口自动化-缺口清单](automation_api_requests_pytest/docs/接口自动化-缺口清单.md) | 对照标准框架的 P0/P1/P2 缺口与完成情况 |
| [AI 助手模块-迭代记录](automation_api_requests_pytest/docs/AI助手模块-迭代记录.md) | AI 测试的演进、踩坑、指标 |
| [AI 助手评测能力对照](automation_api_requests_pytest/docs/AI助手-评测能力对照-已做到与未做到.md) | 六工位评测矩阵与证据 |
| [需求文档](docs/健康饮食推荐系统-需求文档.md) | 业务背景与功能需求 |
| [AI 测试练习路线图](docs/AI测试练习路线图.md) | AI 测试学习 / 实践路线 |

---

## 十、常见问题

### 1. 自动化测试直接中止，提示“环境未就绪”

按启动顺序检查：

1. MySQL 3306 是否在跑；
2. 后端 8080 是否启动，且 `DB_NAME=health_diet_test`；
3. 算法服务 5000 是否启动，`GET /api/kb/stats` 是否 200。

预检会逐项打印 ✔/✘ 和启动命令，不会让你猜。

### 2. 后端连错库

现象：登录返回的 `userId/username` 与测试库不一致，预检中止。

处理：

```bash
set DB_NAME=health_diet_test
# 重启后端
```

### 3. 测试库是新建的，健康档案为空导致用例失败

不要复制开发库。执行：

```bash
database\rebuild_test_db.bat
```

`seed_test.sql` 已显式包含主账号的 `health_info` 和 `health_info_history`，不依赖开发库历史数据。

### 4. AI 助手返回固定错误文案 / p1 用例被跳过

没有配置 `DEEPSEEK_API_KEY`。设置后重启后端；CI 里把它配成 Repository Secret。

### 5. 算法服务 5000 起不来 / RAG 检索为空

- 检查 `algorithm/.venv` 依赖是否安装；
- 首次访问 `/api/kb/stats` 会构建索引，稍等；
- 改了 `权威文件/` 后先跑 `ingest_authority.py`，再调 `/api/kb/reload`。

### 6. 前端请求 404 / 跨域

- 确认后端在 8080；
- `frontend` 的 Vite 已代理 `/api`；
- `front2` 使用 5174，代理配置同样指向 8080。
