# UI 自动化（Playwright + Page Object）

覆盖 **登录 / 健康档案 / 饮食记录 / AI 对话** 四条主流程，共 14 条用例。
登录态走 **接口取 token 直注**（跳过 UI 登录），失败自动留截图与 trace，按周随回归跑。

被测前端是 `front2/`（Vue 3 + Vite 5，端口 5174）。老版 `frontend/` 已退役，
它那套用例随之删除 —— 同一场景维护两份、改一处要改两处，收益抵不过成本。

---

## 1. 快速开始

```bash
# ① 装依赖（本机 Python 3.8，pip 会自动选最后一个兼容的 Playwright 1.48）
"C:\Users\Acer\AppData\Local\Programs\Python\Python38\python.exe" -m pip install -r requirements.txt

# ② 下浏览器内核（约 120MB，只需一次）
python -m playwright install chromium

# ③ 起被测系统：后端 8081 + 前端 5174
#    后端：backend/start-backend.bat
cd ..\front2 && npm run dev
```

跑：

```bash
cd automation_ui_playwright_pytest
python -m pytest                     # 全量（14 条，约 30s）
python -m pytest -m smoke            # 冒烟：登录 + 档案（不调模型）
python -m pytest -m weekly           # 每周回归（含 AI 两条）
python -m pytest test_cases/auth     # 单个模块
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
| `conftest.py` | 浏览器三层对象、登录态夹具、失败留痕、分层标记（自动挂，用例里不写装饰器） |
| `common/auth_state.py` | 接口登录拿 token、拼 `sh_session` 注入脚本、健康档案预建 |
| `common/artifacts.py` | 截图 / trace / 页面文本留存，挂 Allure |
| `pages/base_page.py` | POM 底座：导航、DOM 定位辅助（`.field` / `.seg` / `.chip` / toast / modal）、断言封装 |
| `pages/{login,health_profile,diet_record,assistant}_page.py` | 一个页面一个文件，只放"怎么操作这个页面" |
| `test_cases/auth/` | **唯一真走登录表单**的一组（7 条），token 直注的对照组 |
| `test_cases/health/` | 档案回显 / 修改保存 / 前端校验（3 条） |
| `test_cases/record/` | 饮食记录增删 + 校验（2 条） |
| `test_cases/assistant/` | AI 对话：正常问答 + 护栏（2 条，`slow_ai`） |
| `config/config.py` | 地址、账号、超时、档案基线 —— 全部可用环境变量覆盖 |

---

## 3. token 直注是怎么做的（整套东西的核心）

**这个前端只存一个 key**：

```
localStorage['sh_session'] = { userId, username, email, phone, role, avatar, token }
```

登录成功时 `stores/app.js` 的 `enter(res.data)` 就是这么写的 —— 注入内容和真实登录
产生的是**同一个东西**，这也是"直注等价于登录"最硬的证据：

```python
ctx.add_init_script(script=...)   # 必须在 new_page / goto 之前
```

`add_init_script` 注册在 context 上，页面自己的 JS 跑之前先执行 —— pinia 的 store
一上来就读 localStorage，晚一步就等于"人已经进登录页了才补票"。

三个必须踩对的点：

1. **key 名必须和 `http.js` 的 `SESSION_KEY` 字面一致**。写错的症状很隐蔽：守卫读不到
   session 就送回 `/login`，看起来像"token 无效"。
2. **localStorage 按 origin 隔离**：token 要写在 5174 的 origin 下，写去后端端口没用。
3. **用 `json.dumps` 序列化，别手拼**：中文、引号、U+2028 都会把 JS 字符串截断。

**为什么这是测试准备、不是测试对象**：直注跳过了登录，所以 `test_cases/auth/` 那 7 条
必须真走表单。那组是直注的对照组 —— 它红了，说明被跳过的那段坏了。

另一个价值不只是快：它能指定"已登录 / 未登录"，路由守卫的规则只有这样才测得到。

---

## 4. 失败留痕

| 产物 | 位置 | 用途 |
|---|---|---|
| 截图 | `artifacts/screenshots/<用例名>.png` | 失败瞬间长什么样 |
| trace | `artifacts/traces/<用例名>.zip` | 时间轴回放：每步 DOM 快照 + 网络 + console |
| 页面文本 | 挂在 Allure 附件里 | 断言失败时"页面上到底写了啥" |

```bash
python -m playwright show-trace "artifacts/traces/xxx.zip"
```

截图是在 `pytest_runtest_makereport` 的 call 阶段失败瞬间抓的，不是 fixture 收尾时 ——
teardown 时用例可能已经清完场，最该看的那一屏没了。

---

## 5. 分层与每周回归

| 标记 | 范围 | 用途 |
|---|---|---|
| `smoke` | auth + health | 提交前快速跑，不调模型 |
| `regression` / `weekly` | 全部 | 日常 / 每周回归 |
| `slow_ai` | assistant | 依赖模型，慢且波动 |
| `ui_form_login` | auth | 真走登录表单 |
| `needs_profile` | health | 依赖库里存在完整档案 |

标记按目录自动挂（`conftest.pytest_itemcollected`），加新目录只改那三张表。

---

## 6. CI（GitHub Actions）

`.github/workflows/ui-tests.yml`，只在 GitHub 仓库上触发（Gitee 不跑 Actions）。

| 触发 | 跑什么 |
|---|---|
| push / PR（改了 UI 套件、front2、backend、database） | `-m smoke` |
| 每周五 23:00（北京时间，错开接口层 1 小时） | `-m weekly` |
| 手动 workflow_dispatch | 选 smoke / weekly |

CI 里把整套被测系统拉起来：MySQL(3306) → 算法服务(5000) → 后端 **8081**
（与 front2 的 vite proxy target 一致，不是接口层 CI 的 8080）→ front2 dev server(5174)。

产物两级：

- **Artifacts**：allure-results + 失败截图 / trace / 视频 + 服务日志（保留 14 天）
- **Allure 报告**发布到 gh-pages，与接口层报告共存，统一入口：
  `https://liujunhao-4488.github.io/healthy-automation_api_requests_pytest/`
  （入口页两张卡片 → 接口层 `./api/`，UI `./ui/`）

可选 Secret：`DEEPSEEK_API_KEY` —— 配了 AI 两条真跑，没配则自动 skip 并写明原因。

---

## 7. 已踩过的坑

| 现象 | 原因 |
|---|---|
| 注入了 token 还是被踢回登录页 | `sh_session` 的 key 名或字段清单和前端不一致 |
| `get_by_role(name="健康档案")` 命中两个元素 | 默认是**子串**匹配，会命中空态标题"还没有健康档案" → 传 `exact=True` |
| `filter(has_text=^注册$)` 永远不中 | Vue 模板渲染的按钮 innerText 带换行缩进 → 用可访问名匹配（会做空白归一化） |
| 点"添加"点到别的地方 | 卡片里有两个同名按钮（头部 + 空态）→ 必须圈 `.card-hd` 作用域 |
| 等待 AI 回复提前通过 | 流式占位气泡也匹配 `.msg:not(.user)` → 等 `.stream-text` 消失、正文非空才算落定 |
| 探活显示服务活着，用例却整片超时 | requests 默认走环境代理，"没起"被代理翻成 502 → `session.trust_env = False` |
| `127.0.0.1:5174` 连不上 | Vite 只绑 `::1` → 统一用 `localhost` |
| `-m smoke` 一条也选不中（Windows） | nodeid 用反斜杠，`split("/")` 切不出模块名 → 先 `replace("\\", "/")` |

---

## 8. 已知缺陷 / 下一步

**已知缺陷（2026-11-07 发现，未修）**：AI 助手页的"试试医疗越界问题"按钮发的是
「帮我开个降脂药处方」，但后端 `BLOCK_MEDICAL_PATTERNS` 没有覆盖「开药 / 处方」的规则
—— 问题直达模型，模型自己礼貌拒绝，回答走正常通道、没有拦截样式。
页面文案却承诺"涉及诊断、用药与处方的问题会被安全护栏拦截"。

用例因此标 `xfail`（不是 fail）：已知缺陷不该污染每周回归的信噪比；后端补上规则后
它会变成 **XPASS**，届时删掉测试里的 `xfail` 即可。

下一步，按性价比排序：

1. **修上面那个护栏规则**（后端加一条 `开.{0,6}(药|处方)` 之类的 pattern），
   或者把前端演示问题换成规则表真正覆盖的表述 —— 两者选一，本质是"文案与规则对齐"。
   ✅ 修完 `pytest -m weekly` 里会出现 XPASS 提示。
2. **给关键元素加 `data-testid`**（`<input data-testid="login-email">`）。现在全靠
   placeholder 和文案定位，文案一改选择器就断。这是可测性改进，该提给前端 ——
   在简历里它比多写 20 条用例更能说明问题。
3. 补一条"删除记录后统计同步变化"的用例：现在只验了列表里消失，
   没验聚合数字（BMI、当日热量）跟着变，这类"局部刷新漏了"的缺陷最容易漏。
