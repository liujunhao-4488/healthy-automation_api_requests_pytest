# test_cases/ai_assistant/conftest.py
# AI 助手用例的专用夹具。
#
# 为什么单独放一个 conftest？因为这个模块的夹具和别的模块长得不一样——
# 别的模块测完不用收拾，这里**每聊一句就会在库里多一个会话**，
# 所以必须"边跑边登记，跑完统一删"。
#
# 清理手段用的是接口自带的 DELETE（软删除），不去动数据库——
# 能走接口解决的事，就不绕过接口直接改库。

import uuid
from pathlib import Path

import pytest

from common import cleanup, db, eval_record
from common.logger import log_qa

_HERE = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items):
    """AI 用例的清理要硬删会话/账号，统一标记为 requires_db。

    ⚠️ conftest 的 hook 会收到**全量** items，必须按路径过滤，
    否则会把别的模块也一起标成 requires_db（实测踩过）。
    """
    for item in items:
        if Path(str(item.fspath)).resolve().parent == _HERE:
            item.add_marker(pytest.mark.requires_db)


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

    ⚠️ 这里还兼着**评测留痕**的活（见 common/eval_record.py）：
       每次问答都把 intent / source / blocked / 回答全文存一份，跑完落 JSON。
       它是**旁路** —— 只读不写，不影响任何断言；记录失败也不会让用例变红。
       放在这里而不是各用例里，是因为"所有 AI 行为用例问模型都得经过这个夹具"，
       一处埋点覆盖全部，用例一行都不用改。
    """
    created = []
    turn = 0

    def _ask(text, conversation_id=None):
        nonlocal turn
        payload = {"rawPrompt": text}
        if conversation_id is not None:
            payload["conversationId"] = conversation_id

        body = api.assert_ok(api.assistant.chat(payload, headers=auth_headers),
                             "发送聊天消息应成功")

        cid = body["data"]["conversationId"]
        if cid not in created:
            created.append(cid)
            cleanup.register_conversation(cid)

        # 把这一问一答记进日志 —— AI 接口的价值全在 200 的 body 里，
        # 而 base_api_client 只在 4xx/5xx 时才附 body，正好漏掉它。
        am = body["data"]["assistantMessage"]
        log_qa(text, am["text"])

        turn += 1
        eval_record.observe(text, am, turn=turn, conversation_id=cid)

        return body["data"]

    yield _ask

    # ---- 清理：用例跑完才轮到这儿 ----
    # 先走接口软删（产品行为），再硬删库里的消息/会话行 ——
    # 只软删的话 is_deleted=1 的行会一直堆在主账号名下。
    cleanup.delete_conversations(api, auth_headers, created)


@pytest.fixture
def conversation(api, auth_headers):
    """直接建一个**空会话**（不聊），跑完删掉。返回会话的 data。"""
    body = api.assert_ok(api.assistant.create_conversation({}, headers=auth_headers),
                         "创建会话应成功")
    cid = body["data"]["id"]
    cleanup.register_conversation(cid)

    yield body["data"]

    cleanup.delete_conversations(api, auth_headers, [cid])


@pytest.fixture
def other_user(api):
    """造一个**独立账号 B**，并在 B 名下建一个**有内容**的会话，供越权用例当靶子。

    为什么要独立账号，而不是继续用 `conversationId: 999999`：
      · 999999 测的是「会话不存在」——后端完全可以在查库之前就拒掉；
      · 真越权测的是「会话**存在**，但不是你的」——只有这种样本才能验证
        `AssistantChatServiceImpl.requireConversation()` 里那句
        `!userId.equals(conversation.getUserId())` 真的生效。
      两者失败后果差得很远：前者顶多是报错不友好，后者是**数据泄漏**。

    为什么 B 的会话里必须先聊一句：
      空会话对任何用户都是空的。就算归属校验整段漏了，A 读到的也只是 `[]`，
      用例照样绿——这是典型的假绿。塞一条消息进去，漏校验时才会真的读到别人的东西。

    清理顺序：**先删会话，再删账号**。反了会留下无主会话污染统计。
    不管用例成功还是失败，清理都执行（同 ask 夹具的原理）。
    """
    uniq = "ot_" + uuid.uuid4().hex[:10]
    data = {"username": uniq, "password": "123456", "email": uniq + "@example.com"}
    reg = api.assert_ok(api.auth.register(data), "注册越权靶子账号应成功")

    headers = {"Authorization": "Bearer " + reg["data"]["token"]}
    conv = api.assert_ok(api.assistant.create_conversation({}, headers=headers),
                         "靶子账号建会话应成功")
    cid = conv["data"]["id"]

    # 塞一条真实消息：不关心它答什么，只关心"这个会话里有别人的数据"。
    api.assert_ok(api.assistant.chat({"conversationId": cid, "rawPrompt": "你好"},
                                     headers=headers),
                  "靶子账号发消息应成功")

    user = {
        "userId": reg["data"]["userId"],
        "email": data["email"],
        "headers": headers,
        "conversationId": cid,
    }
    cleanup.register_user(user["userId"], user["email"])
    cleanup.register_conversation(cid)
    yield user

    # ---- 清理 ----
    # ① 先走接口软删除：和产品行为保持一致，也顺带验证 B 自己能删自己的会话。
    # ② 再在库里硬删消息/会话：后端 deleteConversation 只是把 is_deleted 置 1，
    #    行还在，外键 fk_assistant_conversation_user 会挡住下面删账号（1451）。
    #    所以光调接口清不干净，必须补这一步。
    # ③ 最后删账号。顺序不能反：assistant_message → assistant_conversation → user。
    try:
        api.assistant.delete_conversation(cid, headers=headers)
    finally:
        # 按会话删消息，而不是按 user_id：万一越权用例真的把 A 的消息写进了
        # B 的会话，那条消息的 user_id 是 A，按 B 的 user_id 删会漏掉，
        # 接着删会话时又会被 fk_assistant_message_conversation 挡住。
        db.execute(
            "DELETE FROM `assistant_message` WHERE `conversation_id` IN "
            "(SELECT `id` FROM `assistant_conversation` WHERE `user_id` = %s)",
            (user["userId"],),
        )
        db.execute(
            "DELETE FROM `assistant_conversation` WHERE `user_id` = %s",
            (user["userId"],),
        )
        db.execute("DELETE FROM `user` WHERE `id` = %s", (user["userId"],))
        cleanup.unregister_conversations([cid])
        cleanup.unregister_user(user["userId"])
