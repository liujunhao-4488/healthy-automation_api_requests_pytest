# tools/allure_selftest/test_allure_check.py
# 只为验证 Allure 报告本身的"失败/分类/附件"是否正常，**不是业务用例**。
# 故意做成会红的集合：跑它只是为了看一眼报告的分类对不对，别混进 test_cases 一起跑。
# 用法：pytest tools/allure_selftest --alluredir reports/allure-selftest
#      再 python tools/reports/allure_report.py --results reports/allure-selftest

import pytest
import requests

from api import Api
from config.config import TEST_USER


def test_passes_with_attachments(api):
    """一条正常的用例：报告里应该带「请求 / 响应」两个附件、severity=critical。"""
    body = api.assert_ok(api.auth.login(TEST_USER))
    assert "token" in body["data"]


def test_assertion_failure(api):
    """故意断言失败：应被归到「断言不符：接口行为与预期不一致」分类。"""
    body = api.assert_ok(api.auth.login(TEST_USER))
    assert body["message"] == "这条是故意写错的期望值", "故意失败：用来看分类和失败详情"


def test_connection_error():
    """故意打一个没人监听的端口：应被归到「环境问题：后端 / 数据库没起」。"""
    requests.get("http://127.0.0.1:59999/api/whatever", timeout=2)


@pytest.mark.xfail(reason="演示：已知缺陷，等着后端修（xfail 固化）", strict=False)
def test_known_defect():
    """xfail：报告里应是 skipped + 「已知缺陷」分类，且**不算失败**。"""
    assert False, "已知缺陷：故意失败"


@pytest.mark.parametrize("question", ["我能吃海虾吗"], ids=lambda q: q)
def test_ai_qa_attachment(api, auth_headers, question):
    """AI 问答附件：报告里除了请求/响应，还该多一个「问答」文本附件。"""
    body = api.assert_ok(api.assistant.chat({"rawPrompt": question}, headers=auth_headers))
    api.assistant.delete_conversation(body["data"]["conversationId"], headers=auth_headers)
