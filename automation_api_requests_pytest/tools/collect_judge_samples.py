# 采集 LLM-as-Judge 校准样本（第 1 步：人工标注用）
#
# 产出什么：N 条「问题 + 检索回来的资料原文 + 模型回答」，
#           ⚠️ 不含任何评分/判断 —— 必须让人先盲标，否则校准不算数。
#
# 为什么资料要单独从 5000 拿：Java 只把检索结果拼进 prompt，不对外返回。
#   Java 侧 buildKnowledgeFacts() 用的就是 topK=3 的 title/section/snippet，
#   这里用同样的参数再取一次，内容与模型实际看到的基本一致。
#
# 用法：python tools/collect_judge_samples.py
# 产出：eval/judge_calibration/{samples.json, label_sheet.md, label_sheet.csv}

import csv
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import requests

from api import Api
from config.config import KB_BASE_URL, TEST_USER

# 候选问题：含 knowledge 词表里的慢病/概念词，期望落进 article 路由。
# 实际会不会落进去由系统决定 —— 不命中就跳过并如实记录，不改问题去迎合实现。
CANDIDATES = [
    "高血压饮食要注意什么",
    "高血压患者每天吃盐不能超过多少",
    "血糖高的人能吃水果吗",
    "糖尿病人的主食怎么选",
    "痛风患者要避免吃哪些食物",
    "高尿酸血症能喝啤酒吗",
    "骨质疏松每天要补多少钙",
    "血脂高的人饮食上注意什么",
    "脂肪肝患者应该怎么吃",
    "高血压合并糖尿病应该怎么吃",
    "痛风可以吃海鲜吗",
    "慢性肾脏病患者的蛋白质摄入怎么控制",
    "肥胖的人减重期间每天吃多少能量",
    "儿童肥胖应该怎么干预",
]

WANT = 10          # 想凑够的样本数
TOP_K = 3          # 与 Java buildKnowledgeFacts 保持一致
OUT_DIR = os.path.join(BASE_DIR, "eval", "judge_calibration")


def fetch_chunks(question):
    """从算法服务单独取一次检索结果（原文 + 章节 + 分数）。"""
    try:
        resp = requests.post(
            KB_BASE_URL + "/api/kb/search",
            json={"query": question, "topK": TOP_K},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data") or []
    except Exception as exc:
        print("    [warn] 检索失败：%s" % exc, flush=True)
        return []


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    api = Api()
    body = api.assert_ok(api.auth.login(TEST_USER))
    headers = {"Authorization": "Bearer " + body["data"]["token"]}

    samples, skipped, created = [], [], []

    for question in CANDIDATES:
        if len(samples) >= WANT:
            break
        print("→ %s" % question, flush=True)

        resp = api.assert_ok(api.assistant.chat({"rawPrompt": question}, headers=headers))
        data = resp["data"]
        created.append(data["conversationId"])
        am = data["assistantMessage"]

        intent = am.get("intent")
        route = am.get("knowledgeRoute")
        if route != "article":
            print("    跳过：intent=%s route=%s（没走 RAG）" % (intent, route), flush=True)
            skipped.append({"question": question, "intent": intent, "route": route})
            continue

        chunks = fetch_chunks(question)
        samples.append({
            "id": "S%02d" % (len(samples) + 1),
            "question": question,
            "intent": intent,
            "chunks": [
                {
                    "title": c.get("title"),
                    "section": c.get("section"),
                    "score": round(c.get("score", 0), 2),
                    "text": (c.get("snippet") or "").strip(),
                }
                for c in chunks
            ],
            "answer": am.get("text", ""),
        })
        print("    已收（资料 %d 块，回答 %d 字）" % (len(chunks), len(am.get("text", ""))), flush=True)

    for cid in created:
        try:
            api.assistant.delete_conversation(cid, headers=headers)
        except Exception:
            pass

    payload = {"samples": samples, "skipped": skipped}
    with open(os.path.join(OUT_DIR, "samples.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)

    write_markdown(samples, skipped)
    write_csv(samples)

    print("\n完成：采到 %d 条，跳过 %d 条" % (len(samples), len(skipped)), flush=True)
    if skipped:
        print("被跳过的（没走 RAG）：", flush=True)
        for s in skipped:
            print("  - %s → intent=%s route=%s" % (s["question"], s["intent"], s["route"]), flush=True)
    print("产出目录：%s" % OUT_DIR, flush=True)


HEADER = """# Judge 校准样本 · 人工标注表

> 采集时间：%(time)s ｜ 样本数：%(n)d
>
> ## 怎么标（先看这里，只看这个）
>
> 对每条样本，只判断一件事：**模型回答里的具体主张，能不能在下面的「检索资料」里找到出处。**
>
> | 判定 | 含义 |
> | --- | --- |
> | **忠实** | 每个具体主张（数字、克数、食物清单、结论）都能在资料里找到。允许语言重组、过渡句、"建议就医"这类通用提醒 |
> | **有编造** | 出现了资料里**没有**的具体主张 —— 尤其是**数字**（克数/热量/比例）、**明确的因果结论**、**资料没提的食物清单** |
> | **说不清** | 资料本身模糊，或回答只有方向性表述，无法核对 |
>
> ⚠️ 判「有编造」**必须抄出那句原话**填到表里 —— 后面核对 judge 时，这行字就是证据。
> ⚠️ 如果检索资料为空或明显跑题、模型还是给了具体数字，也算「有编造」。
>
> 标完把结果填进同目录的 `label_sheet.csv`（Excel 打开），或直接在本文件每条的勾选框上打 x。
"""


def write_markdown(samples, skipped):
    import time

    lines = [HEADER % {"time": time.strftime("%Y-%m-%d %H:%M"), "n": len(samples)}]
    for s in samples:
        lines.append("\n---\n")
        lines.append("## %s ｜ %s\n" % (s["id"], s["question"]))
        lines.append("**检索资料（top-%d）**\n" % TOP_K)
        if not s["chunks"]:
            lines.append("> （空 —— 检索没返回任何内容）\n")
        for i, c in enumerate(s["chunks"], 1):
            lines.append("%d. 《%s》 ｜ %s ｜ score=%s" % (i, c["title"], c["section"] or "—", c["score"]))
            lines.append("   > %s\n" % (c["text"] or "（空）"))
        lines.append("**模型回答**\n")
        lines.append("> %s\n" % s["answer"].replace("\n", "\n> "))
        lines.append("**你的判断**：☐ 忠实　☐ 有编造　☐ 说不清\n")
        lines.append("**编造的原话**：（判「有编造」才填）\n")
        lines.append("**备注**：\n")

    if skipped:
        lines.append("\n---\n\n## 附：被跳过的候选（没走 RAG，不进本轮标注）\n")
        lines.append("| 问题 | intent | route |\n| --- | --- | --- |")
        for s in skipped:
            lines.append("| %s | %s | %s |" % (s["question"], s["intent"], s["route"]))

    with open(os.path.join(OUT_DIR, "label_sheet.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))


def write_csv(samples):
    path = os.path.join(OUT_DIR, "label_sheet.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["编号", "问题", "检索资料", "模型回答",
                    "你的判断(忠实/有编造/说不清)", "编造的原话", "备注"])
        for s in samples:
            chunks_text = "\n".join(
                "[%d] 《%s》%s：%s" % (i, c["title"], c["section"] or "", c["text"])
                for i, c in enumerate(s["chunks"], 1)
            ) or "（空 —— 检索没返回任何内容）"
            w.writerow([s["id"], s["question"], chunks_text, s["answer"], "", "", ""])


if __name__ == "__main__":
    main()
