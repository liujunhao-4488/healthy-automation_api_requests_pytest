# UI 自动化（Playwright + Page Object）

被测前端是 `front2/`（Vue 3 + Vite 5，端口 5174），共 **8 个业务域 / 32 条用例**。
登录态走 **接口取 token 直注**（跳过 UI 登录），失败自动留截图与 trace，按周随回归跑。

覆盖的业务对象：

| 域 | 覆盖的业务 | 条数 |
|---|---|---|
| `auth` | 登录 / 注册 / 会话保持 / 路由守卫 | 7 |
| `health` | 健康档案（回显、修改、校验） | 3 |
| `record` | 饮食记录（增删、校验） | 2 |
| `assistant` | AI 对话（问答、安全护栏） | 2 |
| `goal` | 饮食目标（类型、热量、营养素配平、持久化） | 5 |
| `account` | 个人资料 / 饮食偏好 | 4 |
| `recipe` | 自定义食谱（增 / 改 / 删 / 搜索） | 5 |
| `article` | 发布文章 / 文章互动（点赞） | 4 |

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
python -m pytest                     # 全量（32 条，约 75s）
python -m pytest -m smoke            # 冒烟：不依赖模型的 7 个域（30 条，约 65s）
python -m pytest -m weekly           # 每周回归（全部，含 AI 两条）
python -m pytest test_cases/goal     # 单个域
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
| `conftest.py` | 浏览器三层对象、登录态夹具、数据清理夹具、失败留痕、分层标记（自动挂，用例里不写装饰器） |
| `common/auth_state.py` | 接口登录拿 token、拼 `sh_session` 注入脚本、健康档案预建 |
| `common/artifacts.py` | 截图 / trace / 页面文本留存，挂 Allure |
| `common/cleanup.py` | **用例建的业务数据自己删**（食谱 / 文章 / 恢复原值），见第 6 节 |
| `common/seed.py` | 前置数据走接口造（编辑/删除类用例只测被测动作本身） |
| `pages/base_page.py` | POM 底座：导航、DOM 定位辅助（`.field` / `.seg` / `.chip` / toast / modal）、断言封装 |
| `pages/*_page.py` | 一个页面一个文件，只放"怎么操作这个页面"（13 个页面对象） |
| `test_cases/<域>/` | 按业务域分目录，一个域一个文件 |
| `config/config.py` | 地址、账号（含管理员）、超时、档案基线 —— 全部可用环境变量覆盖 |

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
| `smoke` | auth / health / record / goal / account / recipe / article | 提交前跑，**不依赖模型** |
| `regression` / `weekly` | 全部 | 日常 / 每周回归 |
| `slow_ai` | assistant | 依赖模型，慢且波动 |
| `ui_form_login` | auth | 真走登录表单 |
| `needs_profile` | health | 依赖库里存在完整档案 |

标记按目录自动挂（`conftest.pytest_itemcollected`），加新目录只改那几张表。

**为什么 recipe / article 也算 smoke**：它们写业务数据，但写的是自己建的临时数据、
跑完自己删（第 6 节）。把它们排除在 smoke 外的代价是"新业务要等到周五才被验证"，
而 CI 的价值恰恰是"提交时就红"。

---

## 6. 用例数据卫生（写业务数据的域必须遵守）

食谱、文章是**真实数据**，不是 mock。不清理的话每跑一次 weekly 就往测试库堆一批
「UI自动化-173xxxx」，一个月后食谱库翻倍、知识列表全是废稿。

约定：

1. **谁建谁删**，在 `cleanup` 夹具的 teardown 里执行 —— 用例中途失败也删。
2. **删除走接口，不走 UI**：快（0.1s vs 点三下等动画）、稳（不依赖删除按钮选择器）、
   不占用例的断言位（清理失败不该让用例红，只是环境卫生）。
3. **名称带唯一后缀**（`unique` 夹具）。用固定名称的话，第二次跑时"按名称找卡片"
   可能命中上一次的残骸 —— 断言绿了，但这次根本没建成功。这类假绿比红更难查。
4. **账号级状态要快照-恢复**（饮食目标、用户名）：先 GET 原值，teardown 走接口写回。
5. **偏好类用"确保选中"而不是"切换一次"**：切换写法会让用例依赖上一次跑的结果，
   单条重跑就红。
6. **前置数据走接口造**（`common/seed.py`）：编辑/删除类用例如果连"建"都走 UI，
   建流程一坏就三条一起红，分不清哪一步坏的。

---

## 7. CI（GitHub Actions）

`.github/workflows/ui-tests.yml`，只在 GitHub 仓库上触发（Gitee 不跑 Actions）。

| 触发 | 跑什么 |
|---|---|
| push / PR（改了 UI 套件、front2、backend、database） | `-m smoke`（30 条） |
| 每周五 23:00（北京时间，错开接口层 1 小时） | `-m weekly`（32 条） |
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

## 8. 已踩过的坑

| 现象 | 原因 |
|---|---|
| 注入了 token 还是被踢回登录页 | `sh_session` 的 key 名或字段清单和前端不一致 |
| `get_by_role(name="健康档案")` 命中两个元素 | 默认是**子串**匹配，会命中空态标题"还没有健康档案" → 传 `exact=True` |
| `filter(has_text=^注册$)` 永远不中 | Vue 模板渲染的按钮 innerText 带换行缩进 → 用可访问名匹配（会做空白归一化） |
| 点"添加"点到别的地方 | 卡片里有两个同名按钮（头部 + 空态）→ 必须圈 `.card-hd` 作用域 |
| 等待 AI 回复提前通过 | 流式占位气泡也匹配 `.msg:not(.user)` → 等 `.stream-text` 消失、正文非空才算落定 |
| 探活显示服务活着，用例却整片超时 | requests 默认走环境代理，"没起"被代理翻成 502 → `session.trust_env = False`（注意 `trust_env` 是 **Session 属性**，写成 `requests.request(..., trust_env=False)` 会 TypeError） |
| `127.0.0.1:5174` 连不上 | Vite 只绑 `::1` → 统一用 `localhost` |
| `-m smoke` 一条也选不中（Windows） | nodeid 用反斜杠，`split("/")` 切不出模块名 → 先 `replace("\\", "/")` |
| 搜索用例读到空标题列表 | 骨架屏也用 `article.recipe-card`（没有 h3），"等第一张卡可见"会命中骨架 → 等 `.sk` 消失 |
| 点"适宜目标"反而把已选项取消了 | 新建表单 `blankForm()` 默认 `fit: ['减脂']` → chip 类控件一律"先读状态，缺了才点" |
| 食谱库页头找不到"新建食谱" | 该按钮在 `v-else` 分支（只在"我的食谱"视图出现），库里是搜索 + 换一批 |
| 文章 / 食谱删除 400「仅管理员可执行该操作」 | 见第 9 节 |

---

## 9. 已知缺陷 / 下一步

**缺陷 1：AI 护栏没覆盖「开处方」**（2026-11-07）
助手页"试试医疗越界问题"按钮发的是「帮我开个降脂药处方」，但后端
`BLOCK_MEDICAL_PATTERNS` 没有覆盖「开药 / 处方」的规则 —— 问题直达模型，模型自己
礼貌拒绝，回答走正常通道、没有拦截样式。页面文案却承诺"涉及诊断、用药与处方的问题
会被安全护栏拦截"。用例标 `xfail`；后端补规则后会自动变 **XPASS**。

**缺陷 2：用户发了文章，自己删不掉**（2026-11-08）
`/article/publish` 只要求登录（发布即上架），但 `/article/delete` 是 `@requireAdmin`。
UGC 没有撤回通道：发错了、发漏了，用户只能找管理员。产品上要么给"作者可删自己的文章"，
要么前端明确提示"发布后不可撤回"。用例的清理因此改走管理员身份。

**缺陷 3：管理员删除文章被外键拦住**（2026-11-08）
即便有管理员权限，`DELETE /article/delete/{id}` 仍然 400：
`SQLIntegrityConstraintViolation` —— 文章被评论 / 点赞 / 阅读历史引用，后端既没有先清
子表也没有级联删除。**这个删除接口实际上是不可用的**。
用例的清理因此降级为"下架"（`status=0`，列表与搜索都不再显示），污染面归零但数据行仍在。

下一步，按性价比排序：

1. 修缺陷 1（后端加 pattern 或换演示问题）—— 修完会出现 XPASS 提示。
2. 修缺陷 3（删除前先清子表，或改级联）—— 修完清理就不必降级为下架。
3. **给关键元素加 `data-testid`**。现在全靠 placeholder 和文案定位，文案一改选择器就断。
   这是可测性改进，该提给前端 —— 在简历里它比多写 20 条用例更能说明问题。
4. 补记录域的聚合联调用例：现在只验"记录删了列表消失"，没验当日热量/BMI 跟着变。
5. 补运营后台（`/admin`）的一套：它走独立登录（`sh_admin_session`）、独立布局，
   是唯一还没覆盖的模块。
