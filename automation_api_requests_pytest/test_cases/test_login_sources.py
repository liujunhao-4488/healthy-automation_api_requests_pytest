# test_cases/test_login_sources.py
# 【任务 #3.5 续：数据源类型谱系】
#
# 同一个登录用例，这次吃 YAML 和 Excel（JSON / CSV 版见 test_login_ddt.py）。
# 把四份数据文件并排看会发现：**业务断言只写一次，换格式不用改一行业务逻辑**。
#
# 格式怎么选：
#   · JSON  —— 程序生成/接口返回；结构灵活，带注释不行
#   · CSV   —— 最通用、Excel 可直接编辑；只能扁平、全是字符串、易踩 BOM
#   · YAML  —— 能写注释、层级表达嵌套；对缩进敏感
#   · Excel —— 测试同学最熟；适合"人来维护"的表格式数据

import pytest

from common.data_loader import load_cases

SOURCES = ["login_cases.yaml", "login_cases.xlsx"]
INT_FIELDS = ["want_http", "want_code"]

CASES = []
for src in SOURCES:
    fmt = src.rsplit(".", 1)[1]
    for row in load_cases(src, int_fields=INT_FIELDS):
        CASES.append(pytest.param(row, id=f"{fmt}-{row['name']}"))


@pytest.mark.parametrize("case", CASES)
def test_login_from_other_sources(api, case):
    """用例完全不知道数据是 YAML 还是 Excel 来的 —— 这就是解耦。"""
    payload = {"email": case["email"], "password": case["password"]}
    resp = api.post("/auth/login", json=payload)

    assert resp.status_code == case["want_http"], f"HTTP 应为 {case['want_http']}，实际 {resp.status_code}"
    body = resp.json()
    assert body["code"] == case["want_code"], f"code 应为 {case['want_code']}，实际 {body.get('code')}"
    assert case["want_msg"] in body["message"], f"message 应含『{case['want_msg']}』"
