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
