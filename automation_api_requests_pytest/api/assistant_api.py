# api/assistant_api.py
# 【接口层】AI 助手：会话管理 + 聊天。
#
# 老规矩：**URL 只写在这个文件里**。用例里只出现 api.assistant.chat(...)。
#
# 这个接口和别的接口有个本质区别，值得单独记一笔：
#   别的接口是"输入 → 固定输出"，这个接口的输出是**一段自然语言**。
#   所以用例没法断言"它答得对不对"，只能断言：
#     · 结构对不对（字段齐不齐、类型对不对）
#     · 行为对不对（该拒绝的有没有拒绝）
#   详见 test_cases/ai_assistant/test_assistant_结构鉴权.py 开头那段说明。
#
# 还有一个坑：/assistant/chat 是**写操作**（会建会话、存消息），
#   所以用例跑完必须清场 —— 见 test_cases/ai_assistant/conftest.py 的 ask 夹具。

import json

from .base_api_client import BaseApiClient


class AssistantApi(BaseApiClient):

    # ---- 聊天 ----

    def chat(self, data, headers=None):
        """POST /assistant/chat —— 发一条消息（需要 token）。

        data 的字段（都来自实测 / 后端源码）：
          · rawPrompt      —— 用户原话（输入框里那句话）
          · prompt         —— 带上下文的完整 prompt（后端会拼健康档案 / 饮食目标）
          · conversationId —— **不传则自动新建一个会话**

        rawPrompt 和 prompt 都为空 → 400「请输入聊天内容」。
        传了不存在的 conversationId → 400「会话不存在或无权访问」。
        """
        return self.post("/assistant/chat", json=data, headers=headers)

    def chat_stream(self, data, headers=None, timeout=120):
        """POST /assistant/chat/stream —— 流式聊天（SSE），**把流读完**再返回整理好的结果。

        为什么要"读完再返回"：用例关心的是"这条流最终说了什么、结构对不对"，
        而不是"每一段的毫秒数"（那是性能测试的活）。把解析放在 api 层，
        用例里就不会出现一行 `iter_lines` —— 传输细节只属于这一层。

        返回一个字典（字段都是从实测的响应里整理出来的，不是猜的）：
          status_code   HTTP 状态码
          content_type  响应头 Content-Type
          events        按到达顺序的全部事件：[(事件名, 数据字典), ...]
          start / done / error   三类事件各取**最后一个**（没出现就是 None）
          deltas        所有 delta 的文本，按顺序
          text          deltas 拼起来的完整文本 —— 正常情况该等于 done 里那条消息的 text
          delta_count   delta 的段数（**它 > 0 不代表流式生效**，见用例里的说明）

        ⚠️ 两个坑，踩过：
          · 一定用 `stream=True`，否则 requests 会把整条流读完才返回 ——
            "能不能流式"这件事就测不到了（会变成永远通过）。
          · 解析必须自己按 UTF-8 解码（`decode_unicode=False`）。
            SSE 的 Content-Type 不带 charset，requests 会按 ISO-8859-1 解，
            中文会变成乱码。
        """
        resp = self.post(
            "/assistant/chat/stream",
            json=data,
            headers=headers,
            stream=True,
            timeout=timeout,
        )

        events = []
        start = done = error = None
        deltas = []
        current = None

        try:
            for raw in resp.iter_lines(decode_unicode=False):
                if raw is None:
                    continue
                line = (raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw).strip()
                if not line:
                    continue
                if line.startswith("event:"):
                    current = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    payload = line[len("data:"):].strip()
                    try:
                        obj = json.loads(payload)
                    except ValueError:
                        continue
                    events.append((current, obj))
                    if current == "start":
                        start = obj
                    elif current == "delta":
                        deltas.append(obj.get("text", ""))
                    elif current == "done":
                        done = obj
                    elif current == "error":
                        error = obj
        finally:
            resp.close()

        return {
            "status_code": resp.status_code,
            "content_type": resp.headers.get("Content-Type", ""),
            "events": events,
            "start": start,
            "done": done,
            "error": error,
            "deltas": deltas,
            "text": "".join(deltas),
            "delta_count": len(deltas),
        }

    # ---- 会话 ----

    def create_conversation(self, data=None, headers=None):
        """POST /assistant/conversations —— 新建会话。

        data 可以不传或传 {}，这时标题会回落成「AI 助手会话」。
        """
        return self.post("/assistant/conversations", json=data or {}, headers=headers)

    def list_conversations(self, headers=None):
        """GET /assistant/conversations —— 当前用户的会话列表（已删的不返回）。"""
        return self.get("/assistant/conversations", headers=headers)

    def list_messages(self, conversation_id, headers=None):
        """GET /assistant/conversations/{id}/messages —— 某会话的全部消息（按时间正序）。

        不存在的会话 / 别人的会话 → 一律 400「会话不存在或无权访问」
        （后端不区分这两种情况，不会告诉你"存在但不是你的"）。
        """
        return self.get(f"/assistant/conversations/{conversation_id}/messages", headers=headers)

    def delete_conversation(self, conversation_id, headers=None):
        """DELETE /assistant/conversations/{id} —— 删除会话（**软删除** is_deleted=1）。

        库里记录还在，只是接口不再返回它 —— 所以用例里可以放心拿它当"清场"手段。
        """
        return self.delete(f"/assistant/conversations/{conversation_id}", headers=headers)
