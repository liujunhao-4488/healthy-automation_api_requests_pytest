# test_cases/account/test_account_ui.py
# 个人中心 —— 基础资料 / 饮食偏好
#
# 这一页和「登录」的区别：登录测的是**会话**，这里测的是**账号资料本身**，
# 而且改完会写进后端 + 同步本地 store（顶栏用户名要立刻变）。
# 这三件事容易各自独立地坏：
#   · 接口存了但 store 没同步 → 刷新才对，不刷新还是旧名
#   · store 同步了但接口没存 → 刷新就回退
# 所以资料类用例的正确断言是「toast + 刷新后仍在」，不是只看提示。
#
# 数据卫生：
#   用户名是账号级状态，改完必须改回去（cleanup.task 走接口恢复）。
#   饮食偏好用「确保选中」的幂等方式，不追求恢复原状 —— 一次开关不值得快照。

import re

from playwright.sync_api import expect

from pages.account_page import AccountPage


class TestProfile:
    def test_修改用户名_保存后刷新仍生效(self, user_page, cleanup, unique):
        """改用户名 → 保存 → 刷新后仍是新名。

        为什么必须刷新：前端的 store.updateProfile 会立刻把顶栏名字换掉，
        所以只看页面上的名字，**接口失败也能"绿"**（乐观更新的假象）。
        刷新会重新 GET /user/profile，拿到的才是后端的真实状态。
        """
        acct = AccountPage(user_page).open()
        acct.expect_loaded()
        acct.open_tab("账号资料")

        original = acct.username()
        new_name = unique("测试名")
        # 用 restore 而不是 task(lambda: api(...))：恢复类动作必须自带成功判据，
        # 否则接口失败会被静默吞掉，账号就永久被改名了（这个坑真踩过）。
        cleanup.restore("PUT", "/user/profile", {"username": original})

        acct.set_username(new_name)
        acct.save_profile()
        acct.expect_profile_saved()

        acct.reload()
        acct.expect_loaded()
        acct.open_tab("账号资料")
        assert acct.username() == new_name, "刷新后用户名回退了，说明只改了本地 store 没落库"

    def test_邮箱是登录凭据_只读不可编辑(self, user_page):
        """邮箱不可改是产品约束（后端也没有改邮箱的接口）。

        断言 readonly 属性而不是"试着填一下报错"：
          只读输入框在浏览器层面就拦住了输入，Playwright 的 fill 会直接超时 30s，
          用异常当判据既慢又分不清"只读"和"元素没找到"。
          再补一次真实键盘输入，确认界面层面也改不动。
        """
        acct = AccountPage(user_page).open()
        acct.expect_loaded()
        acct.open_tab("账号资料")

        email = acct.email_input
        expect(email).to_have_attribute("readonly", re.compile(".*"))

        before = email.input_value()
        email.click()
        user_page.keyboard.type("hacked@example.com")
        assert email.input_value() == before, "只读邮箱被键盘输入改掉了"

    def test_手机号格式非法_前端拦下且请求未发出(self, user_page):
        """手机号是选填项，但填了就必须合法（^1[3-9]\\d{9}$）。

        同样监听网络：前端校验必须在**发请求之前**。
        否则非法手机号会打到后端，前端提示只是"事后告知"。
        """
        acct = AccountPage(user_page).open()
        acct.expect_loaded()
        acct.open_tab("账号资料")

        sent = []
        user_page.on(
            "request",
            lambda r: sent.append(r.url) if r.method == "PUT" and "/user/profile" in r.url else None,
        )

        acct.set_phone("12345")
        acct.save_profile()
        acct.expect_rejected("手机号格式不正确")

        assert not sent, "前端校验没生效：非法手机号已经提交到后端了"


class TestPreference:
    def test_饮食偏好保存_刷新后仍保持(self, user_page):
        """偏好是推荐系统的输入，存不住等于推荐永远按默认跑。

        用「确保选中」而不是「切换一次」：
          偏好的初始状态取决于上一次跑用例的结果，用切换会把断言写成
          "和上一次相反"，用例之间互相依赖，跑单条就红。
          "确保选中 → 保存 → 刷新 → 仍选中"是幂等的，跑多少遍都一样。
        """
        acct = AccountPage(user_page).open()
        acct.expect_loaded()
        acct.open_tab("饮食偏好")

        if not acct.pref_selected("低脂"):
            acct.toggle_pref("低脂")

        acct.save_prefs()
        acct.expect_prefs_saved()

        acct.reload()
        acct.expect_loaded()
        acct.open_tab("饮食偏好")
        assert acct.pref_selected("低脂"), "刷新后「低脂」偏好丢了，说明没落库"
