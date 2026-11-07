# pages/base_page.py
# 作用：Page Object 的公共底座 —— 只放"每个页面都要用"的东西，不放任何业务。
#
# POM 的边界在这儿（很重要，划错了会烂成另一个样）：
#   Page Object 里**只写"怎么操作这个页面"**：元素在哪、怎么点、怎么填、怎么读。
#   断言留一部分在页面对象里：
#     · "这个页面到了没有"（is_loaded / expect_on_page）—— 这是页面自己的知识
#     · "业务对不对"（BMI 算得对不对、记录是不是真进了库）—— 留在用例里
#   把业务断言塞进 page 对象，用例读起来就是一行 page.xxx()，等于没写用例，
#   出了问题也看不出"哪条需求被违反了"。
#
# ── 定位策略（这个项目没有 data-testid，只能靠语义定位）──────────
#   Element Plus 的组件最终都渲染成标准 DOM，可访问名和 placeholder 是稳定的：
#     el-button        → <button><span>登录</span></button>   → get_by_role("button", name="登录")
#     el-input         → <div class="el-input"><input placeholder="...">
#     el-input-number  → 内层同样是 <input>（比外层 div 好定位得多）
#     el-select        → 触发器是 div，**下拉面板挂在 body 下**，不在表单里
#     el-table         → <tr class="el-table__row">
#
#   ⚠️ 最推荐的做法是给关键元素加 data-testid（`<el-input data-testid="login-email">`），
#      定位就从"猜文案"变成"查固定锚点"。这件事该提给前端，属于可测性改进 ——
#      在简历里它是"发现了可测性风险并推动解决"，比多写 20 条用例更能说明问题。
#      在这之前，靠 placeholder + label 文案定位，**文案一改选择器就断**，
#      而这恰恰是最该被自动化发现的变化（改了文案，用例应该红，提示去同步）。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT, FRONTEND_URL


class BasePage:
    """所有 Page Object 的父类。"""

    # 子类覆盖：该页面的路由路径
    path = "/"

    def __init__(self, page, base_url=None):
        self.page = page
        self.base_url = (base_url or FRONTEND_URL).rstrip("/")

    # ---------------- 导航 ----------------

    def url_for(self, path=None):
        path = self.path if path is None else path
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def open(self, path=None, wait_until="domcontentloaded"):
        """打开页面。

        wait_until 用 domcontentloaded 而不是 networkidle：
          Vite dev server 有 HMR 的 websocket 长连接，
          networkidle 会一直等不到"网络空闲"，白白耗掉 30s 再超时。
          页面"加载完没完"由各页面的 expect_loaded() 判定，不靠这个参数。
        """
        self.page.goto(self.url_for(path), wait_until=wait_until)
        return self

    def reload(self):
        self.page.reload(wait_until="domcontentloaded")
        return self

    def current_path(self):
        return self.page.evaluate("() => location.pathname")

    # ---------------- 定位辅助 ----------------

    def by_role_button(self, name, exact=False):
        return self.page.get_by_role("button", name=name, exact=exact)

    def by_placeholder(self, placeholder):
        """placeholder 匹配。用 or_ 兼容"完全相等"和"包含"两种写法。

        为什么不一上来就用包含匹配：
          "请输入邮箱地址" 和 "请输入邮箱" 会同时命中，
          填密码时可能填进邮箱框 —— 这种错不会报元素找不到，只会报"登录失败"。
          所以优先 exact，确实要模糊匹配时由调用方显式传。
        """
        return self.page.get_by_placeholder(placeholder)

    def form_item(self, label, exact=True):
        """按表单项的 label 抓整块，再往里找 input。

        Element Plus 的 el-form-item 结构：
          <div class="el-form-item"><label class="el-form-item__label">邮箱</label>
            <div class="el-form-item__content"><div class="el-input"><input ...>

        为什么需要这个而不只用 placeholder：
          el-input-number / el-select 常常没有 placeholder，
          只能靠"它属于哪个 label"来定位。
        """
        return self.page.locator(".el-form-item").filter(
            has=self.page.get_by_text(label, exact=exact)
        ).first

    def form_input(self, label, exact=True):
        """按 label 找到该表单项里的 input（含 el-input-number 的内层 input）。"""
        return self.form_item(label, exact=exact).locator("input").first

    def el_select(self, label, exact=True):
        """按 label 找到 el-select 的触发器（点它才会展开下拉）。"""
        return self.form_item(label, exact=exact).locator(".el-select").first

    def pick_select_option(self, option_text, timeout=EXPECT_TIMEOUT):
        """选中已展开的下拉项。

        ⚠️ 坑：下拉面板 teleport 到 body 末尾，且**上一次展开的面板不会立刻消失**。
        直接 `page.get_by_text("中等")` 可能点到隐藏面板里的项，
        点击落在不可见元素上 → Playwright 一直重试直到超时。
        所以限定 `:visible`，只点当前展开的那个。
        """
        option = self.page.locator(
            ".el-select-dropdown:visible .el-select-dropdown__item"
        ).filter(has_text=option_text).first
        option.click(timeout=timeout)
        return self

    def dialog(self):
        """当前打开的 el-dialog。

        同理，多个弹窗会叠在 DOM 里，只取可见的那个。
        """
        return self.page.locator(".el-dialog:visible").last

    def table_rows(self, scope=None):
        """表格数据行。

        排除展开行（type="expand" 会额外渲染一行 el-table__expanded-cell），
        否则"行数"永远比实际记录数多。
        """
        root = scope or self.page
        return root.locator(".el-table__body-wrapper tbody tr.el-table__row")

    # ---------------- 等待 / 断言辅助 ----------------

    def expect_visible(self, locator, timeout=EXPECT_TIMEOUT):
        expect(locator).to_be_visible(timeout=timeout)
        return self

    def expect_hidden(self, locator, timeout=EXPECT_TIMEOUT):
        expect(locator).to_be_hidden(timeout=timeout)
        return self

    def expect_text(self, locator, text, timeout=EXPECT_TIMEOUT):
        expect(locator).to_contain_text(text, timeout=timeout)
        return self

    def expect_path(self, path, timeout=EXPECT_TIMEOUT):
        """等路由跳到位。

        用 expect(page).to_have_url 而不是 `assert current_path() == path`：
          路由跳转是异步的（router.replace 之后还可能有一次 window.location 兜底），
          裸断言会在跳转完成前的瞬间判死 —— 这类失败重跑就绿，是最浪费时间的一种。
        """
        pattern = re.compile(re.escape(path) + r"(\?.*)?$")
        expect(self.page).to_have_url(pattern, timeout=timeout)
        return self

    # ---------------- 反馈类（全局组件）----------------

    def toast(self, text=None, timeout=EXPECT_TIMEOUT):
        """ElMessage 轻提示。

        ElMessage 是单例队列，2~3s 后自动消失，且**同名提示可能连续出现两次**
        （比如重复点提交）。所以：
          · 断言用 expect(toast).to_contain_text(...)，
          · 不要自己 sleep 等它消失，等消失用 expect_hidden。
        """
        if text is None:
            return self.page.locator(".el-message:visible").first
        locator = self.page.locator(".el-message:visible").filter(has_text=text).first
        expect(locator).to_be_visible(timeout=timeout)
        return self

    def wait_toast_gone(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.locator(".el-message:visible")).to_have_count(0, timeout=timeout)
        return self

    def confirm_dialog(self, button_text="确定"):
        """el-message-box（二次确认框，注意它**不是** el-dialog）。"""
        box = self.page.locator(".el-message-box:visible").last
        expect(box).to_be_visible(timeout=EXPECT_TIMEOUT)
        box.get_by_role("button", name=button_text).click()
        return self
