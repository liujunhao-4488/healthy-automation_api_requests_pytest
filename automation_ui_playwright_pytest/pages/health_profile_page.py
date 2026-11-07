# pages/health_profile_page.py
# 健康档案（frontend/src/views/HealthInfo.vue 展示 + HealthInfoEdit.vue 编辑）
#
# 两个类放一个文件：它们是同一块业务的"读"和"写"两面，
# 拆成两个文件后总要 import 两个、总记不清哪个有 goto_edit()。
#
# ── 这里最值得设计的不是选择器，是**副作用** ────────────────────
#   档案用例会真的改库里的 weight。改完不还原，下一轮"基线断言"就全错，
#   而现象是"昨天还绿、今天全红"，很难联想到是上一轮留下的数据。
#   所以更新方法统一返回**原值**，由用例在 teardown 里写回去（见 test 文件）。
#   把还原写在 page 对象里是做得到的，但不该做：
#     · 用例可能需要连续改两次，中间不该被自动还原；
#     · "这条用例改了什么、还原了什么"要在用例里看得见。
#
#   另一条路是用接口直接把档案写成基线（更快更稳）。这里刻意走 UI：
#   UI 层要证明的是"**从界面上改，能落库**"，用接口改等于把要测的那段绕过去了。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage


class HealthProfilePage(BasePage):
    """档案展示页 /dashboard/health-info。"""

    path = "/dashboard/health-info"

    def expect_loaded(self):
        self.expect_text(self.page.locator("h2"), "健康信息档案")
        # 三个摘要卡在拿到接口数据后才渲染数值，等它出现即代表"数据到了"
        expect(self.summary_value("当前体重")).not_to_have_text(
            re.compile(r"^--"), timeout=EXPECT_TIMEOUT
        )
        return self

    def summary_value(self, label):
        """摘要卡片上的大数字：当前体重 / BMI 指数 / 基础代谢。

        结构：<div class="summary-card"><div class="summary-meta"><span>当前体重</span></div>
              <strong>70.0 kg</strong></div>
        """
        return self.page.locator(".summary-card").filter(
            has=self.page.get_by_text(label, exact=True)
        ).locator("strong").first

    def info_value(self, label):
        """信息列表项：年龄 / 性别 / 身高 等。

        结构：<div class="info-item"><label>年龄</label><span>26 岁</span></div>
        """
        return self.page.locator(".info-item").filter(
            has=self.page.locator("label", has_text=label)
        ).locator("span").first

    def read_weight(self):
        """读当前体重数值（去掉单位）。

        为什么要剥成数字：页面上是 "70.0 kg"，
        字符串比较会把 "70 kg" 和 "70.0 kg" 判成不同 —— 这属于展示格式差异，
        不是业务错误，用数值比较才不会产生假失败。
        """
        text = self.summary_value("当前体重").inner_text()
        match = re.search(r"[\d.]+", text)
        return float(match.group()) if match else None

    def read_bmi(self):
        text = self.summary_value("BMI 指数").inner_text()
        match = re.search(r"[\d.]+", text)
        return float(match.group()) if match else None

    def read_bmr(self):
        text = self.summary_value("基础代谢").inner_text()
        match = re.search(r"[\d.]+", text)
        return float(match.group()) if match else None

    def goto_edit(self):
        self.by_role_button("修改信息").click()
        page = HealthProfileEditPage(self.page, self.base_url)
        page.expect_loaded()
        return page


class HealthProfileEditPage(BasePage):
    """档案编辑页 /dashboard/health-info/edit。"""

    path = "/dashboard/health-info/edit"

    def expect_loaded(self):
        self.expect_visible(self.by_role_button("保存修改"))
        self.expect_visible(self.form_input("年龄"))
        return self

    # ---- 读写 ----
    def get_number(self, label):
        """el-input-number 的当前值（字符串，'--' 表示空）。"""
        return self.form_input(label).input_value()

    def set_number(self, label, value):
        """填 el-input-number。

        ⚠️ 不能直接 fill：el-input-number 在 blur 时会按 min/max/precision 归一化，
           fill 之后如果不 commit（失焦或回车），组件内部 model 可能仍是旧值，
           点保存写进库的是旧数据 —— 现象是"页面填了 75，库里还是 70"。
           所以填完统一 press("Tab") 让它失焦提交。
        """
        field = self.form_input(label)
        field.fill(str(value))
        field.press("Tab")
        return self

    def set_text(self, label, value):
        self.form_input(label).fill(str(value))
        return self

    def pick_activity(self, option_label):
        """活动水平：点开下拉 → 选可见面板里的选项。"""
        self.el_select("活动水平").click()
        self.pick_select_option(option_label)
        return self

    def set_weight(self, weight):
        return self.set_number("体重", weight)

    def save(self):
        self.by_role_button("保存修改").click()
        return self

    def save_and_expect_success(self):
        """保存并等回到展示页。

        两个断言缺一不可：
          ① 提示"健康信息已更新" —— 证明请求成功
          ② 回到 /dashboard/health-info —— 证明前端状态机走完
        只断提示不断跳转，会漏掉"保存成功但路由没跳"这类缺陷；
        只断跳转不断提示，会漏掉"跳到页了但没真写库"。
        """
        self.save()
        self.toast("健康信息已更新")
        HealthProfilePage(self.page, self.base_url).expect_path("/dashboard/health-info")
        return HealthProfilePage(self.page, self.base_url)
