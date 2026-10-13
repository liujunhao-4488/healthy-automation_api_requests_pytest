# 追问 brevity 探针：验证"后续追问简短作答、不复述档案"
import sys
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/api"

r = requests.post(f"{BASE}/auth/login",
                  json={"email": "2311697186@qq.com", "password": "123456"}, timeout=15)
h = {"Authorization": f"Bearer {r.json()['data']['token']}"}
cid = requests.post(f"{BASE}/assistant/conversations", json={"title": "追问探针"}, headers=h, timeout=15).json()["data"]["id"]

def ask(text):
    resp = requests.post(f"{BASE}/assistant/chat",
                         json={"conversationId": cid, "rawPrompt": text},
                         headers=h, timeout=60).json()
    return resp["data"]["assistantMessage"]["text"]

print("=== 第一轮：我不喜欢吃鸡胸肉 ===")
r1 = ask("我不喜欢吃鸡胸肉")
print(r1[:150], "...\n")
print("=== 第二轮（追问）：鸡胸肉呢 ===")
r2 = ask("鸡胸肉呢")
print(r2)
print(f"\n[追问回复长度] {len(r2)} 字（改前同类追问约 400+ 字）")

requests.delete(f"{BASE}/assistant/conversations/{cid}", headers=h, timeout=15)
