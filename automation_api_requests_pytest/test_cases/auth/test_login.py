# 【任务 #4.2：登录接口 /auth/login（合并版）】
#
# 本文件由 auth/ 下 4 个文件合并而来（原文件已删除，用例一条没丢）：
#   · test_auth.py            → 第 1 组：地基（成功 / 密码错）
#   · test_param_boundary.py  → 第 2 组：参数化 + 边界（该文件里的 /recipe/search 部分已移到 recipe/）
#   · test_login_ddt.py       → 第 3 组：数据驱动（外部文件）+ 第 4 组：fuzz
#   · test_login_sources.py   → 第 3 组：YAML / Excel 两种数据源并入同一组
#
# 为什么要合并：这 4 个文件测的是**同一个接口**（/auth/login），
# 只是分别用了不同的"写法版本"。学习时分开看能看清进化史（裸写 → 参数化 → 外部文件 → 多格式），
# 但交付 / 协作时应该"按接口找用例"——见 README 约定 5、7。
#
# 为什么把两个数据驱动文件并成一组：它们本来就是"同一个用例换数据格式"。
# 合并后一条用例同时吃 JSON / CSV / YAML / Excel 4 种格式，
# 反而更能证明那件事：**业务断言与数据格式无关**。
#
# 本文件用例数：2 + 9 + 24 + 10 = 45

import pytest

from config import TEST_USER
from common.data_loader import load_cases

EMAIL = TEST_USER["email"]
PWD = TEST_USER["password"]


# ===================== 第 1 组：地基 —— 成功 / 失败两条主干 =====================

def test_login_success(api):
    """正常路径：账号密码正确 → 登录成功，返回 token。"""
    resp = api.post("/auth/login", json=TEST_USER)

    # 一行断定"成功"：HTTP 200 + 业务 code==200，并直接拿到解析好的 body
    body = api.assert_ok(resp)
    assert body["message"] == "登录成功"

    # 关键数据：成功登录必须给 token，否则后续接口没法用
    assert "token" in body["data"]
    assert body["data"]["userId"] == 2


def test_login_wrong_password(api):
    """异常路径：密码错误 → 应当被拒绝（业务 code=400）。"""
    wrong = {**TEST_USER, "password": "this_is_wrong"}  # 复制账号，只改密码
    resp = api.post("/auth/login", json=wrong)

    body = resp.json()
    # 密码错属于"业务失败"，文档里登录失败返回 400（见 API.md 第 3 节）
    assert body["code"] == 400
    # 失败时不应下发 token
    assert "token" not in body.get("data", {})


# ===================== 第 2 组：参数化 + 边界/异常 =====================
# @pytest.mark.parametrize —— 让"一条用例"吃"一组输入"。
# 比喻：以前一张卷子只考一道题；现在同一个题目模板，发 N 份"不同数据的答题卡"，
#       每份单独判分（在报告里显示成 N 条独立用例）。
#
# 重要原则：下面所有"期望值"都来自真实跑过后端的结果，不是拍脑袋写的。
#          这正是测试用例的价值——期望必须来自"被测系统的真实契约"。
#
# 每行 = (用例名, 请求体, 期望HTTP, 期望业务code, 期望message包含的内容)
LOGIN_CASES = [
    ("正常登录",   {"email": EMAIL, "password": PWD},              200, 200, "登录成功"),
    ("密码错误",   {"email": EMAIL, "password": "wrong"},          400, 400, "密码错误"),
    ("用户不存在", {"email": "nobody_x@qq.com", "password": PWD},  400, 400, "用户不存在"),
    ("密码为空",   {"email": EMAIL, "password": ""},               400, 400, "密码不能为空"),
    ("缺密码字段", {"email": EMAIL},                                400, 400, "密码不能为空"),
    ("邮箱为空",   {"email": "", "password": PWD},                 400, 400, "邮箱不能为空"),
    ("邮箱格式错", {"email": "not-an-email", "password": PWD},      400, 400, "邮箱格式不正确"),
    ("超长邮箱",   {"email": "a" * 200 + "@qq.com", "password": PWD}, 400, 400, "邮箱格式不正确"),
    ("SQL注入串",  {"email": EMAIL + "' OR '1'='1", "password": PWD}, 400, 400, "邮箱格式不正确"),
]


@pytest.mark.parametrize(
    "case_name, payload, want_http, want_code, want_msg",
    LOGIN_CASES,
    ids=[c[0] for c in LOGIN_CASES],  # 用每行第一列做报告里的用例名，中文可读
)
def test_login_param(api, case_name, payload, want_http, want_code, want_msg):
    """一条函数覆盖 9 种输入：正常 / 密码错 / 缺字段 / 空值 / 格式 / 超长 / 注入。"""
    resp = api.post("/auth/login", json=payload)

    assert resp.status_code == want_http, f"[{case_name}] HTTP 应为 {want_http}，实际 {resp.status_code}"
    body = resp.json()
    print(body)
    assert body["code"] == want_code, f"[{case_name}] code 应为 {want_code}，实际 {body.get('code')}"
    assert want_msg in body["message"], f"[{case_name}] message 应含『{want_msg}』，实际『{body.get('message')}』"


# ===================== 第 3 组：数据驱动（同一用例吃 4 种数据格式）=====================
# 核心一句话：**用例代码只有一份，数据来自外部文件；换数据、换格式都不用改代码。**
# 与第 2 组的区别：那边的数据写死在 .py 里，这边的数据"搬出去了"，业务同学也能改。
#
# 格式怎么选：
#   · JSON  —— 程序生成 / 接口返回；结构灵活，不能写注释
#   · CSV   —— 最通用、Excel 可直接编辑；只能扁平、全是字符串、易踩 BOM
#   · YAML  —— 能写注释、可表达嵌套；对缩进敏感
#   · Excel —— 测试同学最熟；适合"人来维护"的表格式数据
INT_FIELDS = ["want_http", "want_code"]
SOURCES = ["login_cases.json", "login_cases.csv", "login_cases.yaml", "login_cases.xlsx"]

# ---------- L1：数据放在外部文件 ----------
# 这段在"收集阶段"执行：把外部文件读进来，拼成 parametrize 需要的数据列表。
CASES = []
for src in SOURCES:
    fmt = src.rsplit(".", 1)[1]          # "json" / "csv" / "yaml" / "xlsx"
    for row in load_cases(src, int_fields=INT_FIELDS):
        CASES.append(pytest.param(row, id=f"{fmt}-{row['name']}"))


@pytest.mark.parametrize("case", CASES)
def test_login_from_file(api, case):
    """一条用例 × 4 种格式 × 6 行数据 = 24 条。用例自己不知道数据是从哪种格式来的。"""
    payload = {"email": case["email"], "password": case["password"]}
    resp = api.post("/auth/login", json=payload)

    assert resp.status_code == case["want_http"], f"HTTP 应为 {case['want_http']}，实际 {resp.status_code}"
    body = resp.json()
    assert body["code"] == case["want_code"], f"code 应为 {case['want_code']}，实际 {body.get('code')}"
    assert case["want_msg"] in body["message"], f"message 应含『{case['want_msg']}』，实际『{body.get('message')}』"


# ===================== 第 4 组：fuzz（大量数据靠"生成"，不靠手写）=====================
# 思路叫 fuzz（模糊测试）：程序批量造一批非法 / 可疑输入，喂给接口。
# 我们不关心它具体报哪个错，只关心"**系统稳稳拒绝，不 500、不崩、不被注入**"。
FUZZ_CASES = [
    ("空串",       ""),
    ("空格",       " "),
    ("缺@",        "no-at-sign"),
    ("双@",        "a@@qq.com"),
    ("缺本地名",   "@qq.com"),
    ("缺域名",     "a@"),
    ("超长",       "a" * 300 + "@qq.com"),
    ("XSS串",      "<script>alert(1)</script>"),
    ("SQL注入串",  "'; DROP TABLE user; --"),
    ("中文Unicode", "测试@中文.中国"),
]


@pytest.mark.parametrize("case_name, email", FUZZ_CASES, ids=[c[0] for c in FUZZ_CASES])
def test_login_email_fuzz(api, case_name, email):
    """一条用例 × 10 个生成输入：非法输入必须"被拒绝"，绝不能 500。"""
    resp = api.post("/auth/login", json={"email": email, "password": "123456"})
    # 报"邮箱格式不正确"还是"用户不存在"都行，但都必须是 400（业务拒绝）
    assert resp.status_code == 400, f"[{case_name}] 非法邮箱应被拒绝，实际 HTTP {resp.status_code}"
    assert resp.json()["code"] == 400, f"[{case_name}] 业务 code 应为 400"
