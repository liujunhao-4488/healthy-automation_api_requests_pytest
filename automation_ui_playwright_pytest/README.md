# UI 自动化（Playwright + Page Object）

覆盖登录 / 健康档案 / 饮食记录 / AI 对话四条主流程。
登录态走 **接口取 token 直注**，失败自动留截图与 trace，按周随回归跑。

**被测对象有两版前端**：

| | frontend/（老版，Element Plus） | front2/（膳衡重写版，零依赖） |
|---|---|---|
| 地址 | http://localhost:5173 | http://localhost:5174 |
| 登录态存储 | `token` + `health-user` 两份 | `sh_session` 一份 |
| POM | `pages/*_page.py` | `pages/f2_*.py` |
| 用例 | `test_cases/{auth,health,record,assistant}/` | `test_cases/front2/{auth,health,record,assistant}/` |
| 档案门槛 | 守卫按 health-user 判（有引导流） | 守卫只判 isLoggedIn（无引导流） |

两套共用同一份 conftest / auth（同一个后端 8081、同一个测试账号），注入脚本不同
（`common/auth_state.py` vs `common/auth_state_f2.py`）。

---

## 1. 首次运行（三步）

```bash
# ① 装依赖（本机是 Python 3.8，会装到 1.48.0，这是最后一个支持 3.8 的版本）
"C:\Users\Acer\AppData\Local\Programs\Python\Python38\python.exe" -m pip install -r requirements.txt

# ② 下浏览器内核（约 120MB，只需一次）
python -m playwright install chromium

# ③ 起被测系统：后端 8081 + 前端 5173
cd ..\frontend && npm run dev
```

跑：

```bash
cd automation_ui_playwright_pytest
python -m pytest                       # 全量
python -m pytest -m smoke              # 冒烟（不调模型）
python -m pytest test_cases/auth       # 单个模块
python -m pytest --headed              # 看浏览器跑（调试用，需先改 HEADLESS）
```

出报告：

```bash
python -m pytest --alluredir=artifacts/allure-results
allure serve artifacts/allure-results
```

---

## 2. 目录与职责

| 路径 | 职责 |
|---|---|
| `conftest.py` | 浏览器三层对象（browser/context/page）、登录态夹具、失败留痕、分层标记 |
| `common/auth_state.py` | 接口取 token、拼 `health-user`、生成注入脚本 |
| `common/artifacts.py` | 截图 / trace / 页面文本留存，挂 Allure |
| `pages/base_page.py` | POM 底座：导航、Element Plus 定位辅助、断言封装 |
| `pages/*_page.py` | 一个页面一个文件，只放"怎么操作这个页面" |
| `test_cases/auth/` | **唯一真走登录表单**的一组（5 条） |
| `test_cases/health/` | 档案读取 / 编辑 / 路由守卫（7 条） |
| `test_cases/record/` | 饮食记录增删 + 校验（5 条） |
| `test_cases/assistant/` | AI 对话链路（3 条，标记 `slow_ai`） |
| `config/config.py` | 地址、账号、超时、档案基线 —— 全部可用环境变量覆盖 |
| `pages/f2_*.py` | front2 专属 POM（零依赖 DOM，无 Element Plus） |
| `common/auth_state_f2.py` | front2 的 sh_session 注入 + 档案预建 |
| `test_cases/front2/` | front2 四条主流程（14 条） |

---

## 3. token 直注是怎么做的（这是整套东西的核心）

**别只写 `token` 一个键。** 前端存了两处：

```
localStorage['token']       = 裸 JWT
localStorage['health-user'] = 完整用户态 JSON（含 healthInfo / role / userId）
```

路由守卫读的是 `health-user`，不是 `token`。只写 token 的话：

- 访问 `/dashboard` 能进（那条只查 token）
- 但档案相关页面走空态，因为守卫认为"这个用户还没建档案"

注入方式：

```python
ctx.add_init_script(script=...)   # 必须在 new_page / goto 之前
```

`add_init_script` 注册在 context 上，页面自己的 JS 跑之前先执行 —— pinia 初始化一上来就读 localStorage，晚一步就等于"人已经进登录页了才补票"。

**为什么这是测试准备、不是测试对象**：直注跳过了登录，所以 `test_cases/auth/` 那 5 条必须真走表单。那组是直注的对照组 —— 它红了，说明被跳过的那段坏了。

**第二个价值不只是快**：它能指定"已登录 / 未登录 / 有档案 / 没档案"四种状态。路由守卫的三条规则只有这样才测得到（`TestRouteGuard`）。

---

## 4. 失败留痕

| 产物 | 位置 | 用途 |
|---|---|---|
| 截图 | `artifacts/screenshots/<用例名>.png` | 失败瞬间长什么样 |
| trace | `artifacts/traces/<用例名>.zip` | 时间轴回放：每步 DOM 快照 + 网络 + console |
| 页面文本 | 挂在 Allure 附件里 | 断言失败时"页面上到底写了啥" |

看 trace 比看截图有用得多：

```bash
python -m playwright show-trace "artifacts/traces/xxx.zip"
```

截图是在 `pytest_runtest_makereport` 的 call 阶段失败瞬间抓的，不是 fixture 收尾时 —— fixture teardown 时用例可能已经清完场，最该看的那一屏没了。

---

## 5. 分层与每周回归

标记在收集阶段自动挂（按目录推），用例文件里不用写装饰器：

| 标记 | 范围 | 用途 |
|---|---|---|
| `smoke` | auth + health | 提交前快速跑，约 1 分钟 |
| `regression` | 全部 | 日常 |
| `weekly` | 全部 | 每周回归集合 |
| `slow_ai` | assistant | 依赖模型，慢且波动 |
| `ui_form_login` | auth | 真走登录表单 |
| `needs_profile` | health | 依赖库里存在完整档案 |

每周回归用 Windows 计划任务：

```bat
cd /d D:\biyesheji\automation_ui_playwright_pytest
"C:\Users\Acer\AppData\Local\Programs\Python\Python38\python.exe" -m pytest -m weekly --alluredir=artifacts\allure-results
```

已经有一条现成的 Allure 发 Pages 的流程（GitHub `gh-pages`），UI 结果可以并到同一个报告入口，按 `ui / api` 两个 suite 分栏。

---

## 6. 已踩过的坑（写下来省的再踩一次）

| 现象 | 原因 |
|---|---|
| 注入了 token 还是被踢回登录页 | 只写了 `token`，没写 `health-user` |
| 注入后档案页全是空 | `healthInfo` 字段形状不对，或 `activityLevel` 填了 label（"中度活动"）而不是 value（`moderately_active`） |
| 填了日期点不到"餐次" | el-date-picker 的面板没关，挡住下面的下拉 → 填完按 Escape |
| 填了 75，库里还是 70 | el-input-number 必须失焦（Tab）才提交值 |
| 保存后 BMI 不变 | 前端保存后没把重算的 bmi 写回 store（真缺陷，用例专门抓这个） |
| `form_item("日期")` 填错地方 | 筛选区和弹窗里都有 el-form-item，必须限定在 `self.dialog()` 内 |
| 下拉选项点不中 | 面板 teleport 到 body 且旧面板不消失 → 选 `:visible` |
| `networkidle` 一直超时 | Vite 的 HMR websocket 长连接，永远不会 idle → 用 `domcontentloaded` |

---

## 7. 当前状态与下一步

已完成：骨架 + 两版前端共 35 条用例。
老版 21 条（登录 5 / 档案 7 / 记录 5 / AI 3），front2 14 条（auth 7 / health 3 / record 2 / assistant 2）。

front2 跑法：

```bash
cd front2 && npm run dev          # 5174（Vite 只绑 ::1，地址用 localhost 别用 127.0.0.1）
cd automation_ui_playwright_pytest
python -m pytest test_cases/front2              # 全部
python -m pytest test_cases/front2 -m smoke     # auth + health
```

front2 已知环境依赖：
- **AI 对话 2 条**：后端需配置 `DEEPSEEK_API_KEY`。没配时后端所有提问返回
  "模型服务连接失败"降级文案、护栏分类同时失效 —— 用例检测到降级文案会
  **skip 并写明原因**，不会红着冒充缺陷。
- **档案用例**：会话开始时自动用接口预建档案（幂等），不需要手动准备。

⚠️ 老版套件（test_cases/auth 等）当前在本机有 8 条红/错，是历史遗留
（如 `locator("h2")` 同时命中壳层品牌标题和页面标题），与 front2 那套无关。

建议的下一步，按性价比排序：

1. **给关键元素加 `data-testid`**（`<el-input data-testid="login-email">`）。现在全靠 placeholder 和 label 文案定位，文案一改选择器就断。这是可测性改进，该提给前端 —— 在简历里它比多写 20 条用例更能说明问题。
2. 修老版套件的 8 条历史红（多为止步于 strict mode 违规，一天内能清完）。
3. 老版修绿后，把 `test_cases/auth`、`test_cases/health` 加进 CI 范围（见下节）。

---

## 8. CI（GitHub Actions）

`.github/workflows/ui-tests.yml`，只在 GitHub 仓库上触发（Gitee 不跑 Actions）。

| 触发 | 跑什么 |
|---|---|
| push / PR（改了 UI 套件、front2、backend、database） | front2 冒烟（`-m smoke`） |
| 每周五 23:00（北京时间，错开接口层 1 小时） | front2 全量回归（`-m weekly`） |
| 手动 workflow_dispatch | 选 front2-smoke / front2-weekly |

CI 里把整套被测系统拉起来：MySQL(3306) → 算法服务(5000) → 后端 **8081**（与
front2 的 vite proxy target 一致，不是接口层 CI 的 8080）→ front2 dev server(5174)。

产物两级：
- **Artifacts**：allure-results + 失败截图 / trace / 视频 + 服务日志（保留 14 天）
- **Allure 报告**发布到 gh-pages 的 `ui/` 子目录，与接口层报告共存：
  `https://liujunhao-4488.github.io/healthy-automation_api_requests_pytest/ui/`

两个工作流的发布步骤都加了 `keep_files: true`——否则 peaceiris 会把 gh-pages
同步成只剩自己的内容，把对方报告抹掉。这类"两个发布者共写一个分支"的坑，
比测试本身容易翻车。

可选 Secret：`DEEPSEEK_API_KEY`（配了则 AI 对话 2 条真跑，没配自动 skip 并写明原因）。

