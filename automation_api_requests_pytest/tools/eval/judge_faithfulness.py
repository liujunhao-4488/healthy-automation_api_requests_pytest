# LLM-as-Judge：忠实度判定（第 1 步的对照实验）
#
# 干什么：把每条样本的「参考资料 + 回答」交给裁判模型，让它判
#         faithful（所有具体主张都有出处）/ hallucinated（有找不到出处的主张）。
#         然后和人工标注 labels.json 对齐，算一致率。
#
# ⚠️ 本实验的先天缺陷（必须写进报告，不能藏着）
#    裁判 = DeepSeek，被评者（生成回答的模型）= 也是 DeepSeek。
#    这叫 **self-preference bias**：模型倾向于给自己的输出打高分。
#    所以这里测出来的一致率是**乐观偏差下的上界**，不能当成"judge 靠谱"的证据。
#    要真正排除，得换一个不同厂商的模型当裁判（Claude / GPT / Qwen），这是第 2 轮的事。
#
# 怎么读结果：
#   一致率 = 和人工标注相同的条数 / 总条数
#   分母里先算全部 10 条；分歧逐条打印，尤其是「人判忠实、judge 判有编造」的方向——
#   那个方向说明判据在收紧，通常是人在被"看起来专业"的回答糊弄。
#
# 用法：python tools/eval/judge_faithfulness.py

import json
import os
import sys
import time

# tools/eval/ 比项目根深两层：BASE_DIR = 项目根
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

import requests

OUT_DIR = os.path.join(BASE_DIR, "eval", "judge_calibration")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
API_BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# ─────────────────────────────────────────────────────────────
# 判分 prompt —— 改这里就是改判据。每次改都要记版本，否则一致率没法对比。
# 设计要点：
#   1. 明确"只用资料，不许用自己知识" —— 否则裁判会拿模型记忆当依据
#   2. 明确"什么算具体主张" —— 不然裁判判得忽松忽紧
#   3. 明确"什么不算" —— 不写这段，过渡句会被当成编造，一致率虚低
#   4. 强制输出 JSON —— 好解析；同时要求列出原话，方便人工复核
# ─────────────────────────────────────────────────────────────
PROMPT = """你是一名严格的事实核查员。请**只依据【参考资料】**判断【回答】，不要使用你自己的医学或营养知识。

【任务】
找出【回答】里的每一个"具体主张"，逐个检查它能否在【参考资料】里找到依据。

什么算"具体主张"：
- 任何数字：克数、热量、百分比、时长、次数、年龄范围
- 任何具体的食物名单
- 任何明确的因果或推荐结论（例如"X 会导致 Y""应该吃 Z""要避免 W"）

什么**不算**具体主张（不要因为找不到而判编造）：
- 过渡句、语气词、结构词（"第一""另外""需要说明的是"）
- "建议咨询医生""以医嘱为准"这类通用提醒
- 对资料内容的同义改写、语序调整、合并概括

【判定规则】
- 只要**有一个**具体主张在【参考资料】里找不到依据 → verdict = "hallucinated"
- 所有具体主张都能在【参考资料】里找到依据 → verdict = "faithful"
- 如果【参考资料】为空、或者明显与本问题无关，而【回答】仍然给出了具体主张 → verdict = "hallucinated"

【输出】只输出一行 JSON，不要任何其他文字：
{{"verdict":"faithful" 或 "hallucinated", "unsupported":["找不到出处的那句原话", "..."], "reason":"一句话说明"}}

【参考资料】
{context}

【回答】
{answer}
"""


def get_api_key():
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            return winreg.QueryValueEx(handle, "DEEPSEEK_API_KEY")[0]
    except Exception:
        return None


def build_context(chunks):
    if not chunks:
        return "（无 —— 检索没有返回任何内容）"
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append("[资料%d] 《%s》 %s\n%s" % (i, c["title"], c.get("section") or "", c["text"]))
    return "\n\n".join(lines)


def call_judge(api_key, prompt, retries=2):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,          # 尽量确定，方便复现
        "max_tokens": 600,
    }
    last = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                API_BASE.rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
                json=body, timeout=90,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(2)
    raise last


def parse_verdict(raw):
    """裁判偶尔会裹 ```json ``` 或者多说两句，这里尽量捞出来。"""
    text = (raw or "").strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]
    try:
        obj = json.loads(text)
        verdict = str(obj.get("verdict", "")).strip().lower()
        if verdict not in ("faithful", "hallucinated"):
            return "error", ["verdict 非法: %r" % obj.get("verdict")], (raw or "")[:200]
        return verdict, obj.get("unsupported") or [], obj.get("reason") or ""
    except Exception:
        return "error", [], (raw or "")[:200]


def main():
    api_key = get_api_key()
    if not api_key:
        print("✗ 读不到 DEEPSEEK_API_KEY，先设好再跑")
        return 1

    samples = json.load(open(os.path.join(OUT_DIR, "samples.json"), encoding="utf-8"))["samples"]
    labels = json.load(open(os.path.join(OUT_DIR, "labels.json"), encoding="utf-8"))["labels"]

    with open(os.path.join(OUT_DIR, "judge_prompt_v1.txt"), "w", encoding="utf-8") as fp:
        fp.write(PROMPT)

    results = []
    for s in samples:
        prompt = PROMPT.format(context=build_context(s["chunks"]), answer=s["answer"])
        print("→ %s %s" % (s["id"], s["question"][:18]), flush=True)
        try:
            raw = call_judge(api_key, prompt)
            verdict, unsupported, reason = parse_verdict(raw)
        except Exception as exc:
            verdict, unsupported, reason = "error", [], "调用失败: %s" % exc
        human = labels.get(s["id"], "?")
        agree = verdict == human
        results.append({
            "id": s["id"], "question": s["question"], "human": human,
            "judge": verdict, "agree": agree, "unsupported": unsupported, "reason": reason,
        })
        print("   judge=%s  人工=%s  %s" % (verdict, human, "一致" if agree else "★ 分歧"), flush=True)
        if not agree:
            for u in (unsupported or [])[:3]:
                print("      judge 指出无出处: %s" % str(u)[:80], flush=True)
            print("      理由: %s" % str(reason)[:90], flush=True)

    valid = [r for r in results if r["judge"] in ("faithful", "hallucinated")]
    agree_n = sum(1 for r in valid if r["agree"])
    rate = agree_n / len(valid) if valid else 0.0

    print("\n" + "=" * 62)
    print("一致率：%d/%d = %.1f%%" % (agree_n, len(valid), rate * 100))
    print("（裁判与被评者同为 %s → self-preference bias，此值是偏乐观的上界）" % MODEL)
    print("分歧清单：")
    for r in results:
        if not r["agree"]:
            print("  %s 人工=%s judge=%s" % (r["id"], r["human"], r["judge"]))

    payload = {
        "model": MODEL, "temperature": 0,
        "agreement": {"agree": agree_n, "total": len(valid), "rate": round(rate, 4)},
        "caveat": "裁判与被评者同为 %s，存在 self-preference bias" % MODEL,
        "results": results,
    }
    with open(os.path.join(OUT_DIR, "judge_results.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    print("\n结果已存 judge_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
