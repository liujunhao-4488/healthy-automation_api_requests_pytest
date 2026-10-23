# 后端冒烟检查 —— 重启服务后跑一遍，确认三条链路都活着
#
# 为什么要有这个：之前用的是根目录的 `_verify_rag_e2e.py`，下划线开头容易被
# 当成临时草稿清掉（本项目 .gitignore 里就有 `_*` 规则）。冒烟是反复要用的动作，
# 放在 tools/ 下当正式工具更合适。
#
# 查三件事（正好覆盖后端的三种处理路径）：
#   1. article     —— 慢病问题走知识库检索（要 5000 活着）
#   2. ingredient  —— 食材营养数值走查表（不调检索）
#   3. chat        —— 闲聊不查任何数据（对照组）
#
# 用法：python tools/smoke_check.py

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from api import Api
from config.config import TEST_USER

CASES = [
    ("高血压饮食要注意什么", "knowledge", "article"),
    ("鸡胸肉多少卡", "knowledge", "ingredient"),
    ("刚吃了碗牛肉面", "chat", None),
]


def main():
    api = Api()
    try:
        body = api.assert_ok(api.auth.login(TEST_USER))
    except Exception as exc:
        print("✗ 登录失败，后端可能没起来: %s" % exc)
        return 1
    headers = {"Authorization": "Bearer " + body["data"]["token"]}
    print("✓ 登录通过")

    created, bad = [], 0
    for question, want_intent, want_route in CASES:
        data = api.assert_ok(api.assistant.chat({"rawPrompt": question}, headers=headers))["data"]
        created.append(data["conversationId"])
        am = data["assistantMessage"]
        intent, route, source = am.get("intent"), am.get("knowledgeRoute"), am.get("source")
        ok = (intent == want_intent) and (route == want_route)
        if not ok:
            bad += 1
        print("%s %-16s intent=%-9s route=%-10s source=%-8s 期望=%s/%s" % (
            "✓" if ok else "✗", question, intent, route, source, want_intent, want_route))
        print("   回答: %s" % (am.get("text") or "").replace("\n", " ")[:90])

    for cid in created:
        try:
            api.assistant.delete_conversation(cid, headers=headers)
        except Exception:
            pass

    print("\n%s（%d 条，%d 条不符）" % ("全部通过" if bad == 0 else "有不符合项", len(CASES), bad))
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
