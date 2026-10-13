# 临时探针：验证多轮历史是否真的生效（问档案里没有的信息）
import sys
import requests

BASE = "http://127.0.0.1:8080/api"

r = requests.post(f"{BASE}/auth/login",
                  json={"email": "2311697186@qq.com", "password": "123456"}, timeout=15)
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}

conv = requests.post(f"{BASE}/assistant/conversations", json={"title": "记忆探针"}, headers=h, timeout=15).json()
cid = conv["data"]["id"]

def ask(text):
    resp = requests.post(f"{BASE}/assistant/chat",
                         json={"conversationId": cid, "rawPrompt": text},
                         headers=h, timeout=60).json()
    return resp["data"]["assistantMessage"]["text"]

code = "蓝色帆船42号"
print("=== 第一轮：告知暗号 ===")
print(ask(f"请记住一个只有我们知道的暗号：{code}，记住后简单回复好的即可。")[:200])
print("\n=== 第二轮：追问暗号（档案里没有，只能靠历史） ===")
reply2 = ask("我刚才让你记住的暗号是什么？请直接说出来。")
print(reply2[:400])
print("\n=== 判定 ===")
print("PASS：历史生效" if code in reply2 else "FAIL：历史没生效（模型答不出暗号）")

requests.delete(f"{BASE}/assistant/conversations/{cid}", headers=h, timeout=15)
