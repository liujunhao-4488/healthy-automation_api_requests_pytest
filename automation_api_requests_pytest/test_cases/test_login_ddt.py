# test_cases/test_login_ddt.py
# 【任务 #3.5：数据驱动 DDT（Data-Driven Testing）】
#
# 核心一句话：**用例代码只有一份，数据来自外部文件或程序生成；换数据不用改代码。**
# 与 test_param_boundary.py 的区别：那边数据写死在 .py 里，这边数据"搬出去了"。

import pytest

from common.data_loader import load_cases

INT_FIELDS = ["want_http", "want_code"]
SOURCES = ["login_cases.json", "login_cases.csv"]

# ---------- L1：同一份用例，吃两个不同格式的数据文件 ----------
# 这段在"收集阶段"执行：把外部文件读进来，拼成 parametrize 需要的数据列表。
CASES = []
for src in SOURCES:
    fmt = src.rsplit(".", 1)[1]          # "json" / "csv"
    for row in load_cases(src, int_fields=INT_FIELDS):
        CASES.append(pytest.param(row, id=f"{fmt}-{row['name']}"))


@pytest.mark.parametrize("case", CASES)
def test_login_ddt_from_file(api, case):
    """数据来自外部文件。注意：用例自己不知道数据是 JSON 还是 CSV 来的。"""
    payload = {"email": case["email"], "password": case["password"]}
    resp = api.post("/auth/login", json=payload)

    assert resp.status_code == case["want_http"], f"HTTP 应为 {case['want_http']}，实际 {resp.status_code}"
    body = resp.json()
    assert body["code"] == case["want_code"], f"code 应为 {case['want_code']}，实际 {body.get('code')}"
    assert case["want_msg"] in body["message"], f"message 应含『{case['want_msg']}』，实际『{body.get('message')}』"


# ---------- L2：真正"大量数据"靠"生成"，不靠手写 ----------
# 思路叫 fuzz（模糊测试）：程序批量造一批非法/可疑输入，喂给接口。
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
