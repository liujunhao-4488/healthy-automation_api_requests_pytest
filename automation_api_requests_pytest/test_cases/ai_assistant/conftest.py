# test_cases/ai_assistant/conftest.py
# AI 助手用例的专用夹具。
#
# 为什么单独放一个 conftest？因为这个模块的夹具和别的模块长得不一样——
# 别的模块测完不用收拾，这里**每聊一句就会在库里多一个会话**，
# 所以必须"边跑边登记，跑完统一删"。
#
# 清理手段用的是接口自带的 DELETE（软删除），不去动数据库——
# 能走接口解决的事，就不绕过接口直接改库。

import pytest

from common.logger import log_qa


@pytest.fixture
def ask(api, auth_headers):
    """聊一句，返回响应里的 data；本次创建的所有会话在用例跑完统一删掉。

    用法：
        data = ask("我能吃海虾吗")          # 不传会话 id → 自动新建一个会话
        data = ask("那鸡胸肉呢", cid)       # 传 id → 接着上一个会话聊

    返回的是 data（不是 response）——因为用例关心的几乎都是 data 里的东西，
    而"请求成功"这件事交给 assert_ok 在里面判了，用例不用重复写。

    yield 之后 = 清理。**不管用例成功还是失败，清理都会执行**
    （原理见 test_cases/user/test_user_profile.py 里 temp_user 的注释）。
    """
    created = []

    def _ask(text, conversation_id=None):
        payload = {"rawPrompt": text}
        if conversation_id is not None:
            payload["conversationId"] = conversation_id

        body = api.assert_ok(api.assistant.chat(payload, headers=auth_headers),
                             "发送聊天消息应成功")

        cid = body["data"]["conversationId"]
        if cid not in created:
            created.append(cid)

        # 把这一问一答记进日志 —— AI 接口的价值全在 200 的 body 里，
        # 而 base_api_client 只在 4xx/5xx 时才附 body，正好漏掉它。
        log_qa(text, body["data"]["assistantMessage"]["text"])

        return body["data"]

    yield _ask

    # ---- 清理：用例跑完才轮到这儿 ----
    for cid in created:
        api.assistant.delete_conversation(cid, headers=auth_headers)


@pytest.fixture
def conversation(api, auth_headers):
    """直接建一个**空会话**（不聊），跑完删掉。返回会话的 data。"""
    body = api.assert_ok(api.assistant.create_conversation({}, headers=auth_headers),
                         "创建会话应成功")

    yield body["data"]

    api.assistant.delete_conversation(body["data"]["id"], headers=auth_headers)
