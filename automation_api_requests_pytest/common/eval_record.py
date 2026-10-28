# common/eval_record.py
# 【评测留痕】把"这次运行到底发生了什么"攒下来，跑完落一份 JSON。
#
# ══ 为什么需要它（这个文件的全部理由）══
# 以前的 pytest 只留**红绿**。红绿能回答"过了没"，回答不了三个评测问题：
#   · 意图识别**准确率**多少？判错的那些，把 query 判成了什么？→ 要 actual 值
#   · 拦错了没有？→ 要"期望拦"和"实际拦"两个值
#   · 这条越狱是**真守住**还是**被硬拦吃掉**？→ 要 source
# 于是每次想知道这些，就得**重跑一遍**（烧钱、还慢）。
#
# 这个零件把 actual **全文**留痕一次 → 之后改判据、换指标口径，**在 JSON 上重算即可，永不再跑模型**。
# 这就是"报告 ≠ 断言"落到工程上的样子：断言只给红绿，报告要的是数字和证据。
#
# ══ 采集什么 ══
#   ① observations —— 每次问答的真实观测（问题 / intent / source / blocked / **回答全文**）
#   ② outcomes     —— 每个用例的结果（passed / failed / xfailed / error + 原因 + 耗时）
# 两者用 **nodeid** 关联。nodeid 里带参数 id（就是数据集里的 name），
# 所以下游能精确 join 回"这条样本期望什么" —— 不用猜、不用按问题文本模糊匹配。
#
# ══ 设计约束 ══
#   · **纯旁路**：不改变任何测试行为，出问题最多是没记录，不会让用例变红。
#   · 不在 pytest 里跑（比如手工脚本 import 了 ask）时**静默跳过**，不报错。
#   · 只在真采到观测时才落盘 —— 跑一堆非 AI 用例不该把上一份完整评测数据覆盖成空的。

import json
import os
from datetime import datetime
from pathlib import Path

# 项目根（本文件在 common/ 下，往上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 默认落盘位置：tools/eval/eval_results.json（会覆盖 —— 里面记着本次范围，看 meta 就能判断完整度）
DEFAULT_OUT = PROJECT_ROOT / "tools" / "eval" / "eval_results.json"

_current_nodeid = None      # 当前正在跑的用例；由顶层 conftest 在 logstart 时更新
_observations = []          # list[dict]：每次问答一条
_outcomes = []              # list[dict]：每个用例一条


# ==================== 写入侧（测试运行时调） ====================

def reset():
    """清空。会话开始时调一次 —— 保证一次运行只有这一轮的记录。"""
    global _current_nodeid
    _current_nodeid = None
    _observations.clear()
    _outcomes.clear()


def start_case(nodeid):
    """标记"现在在跑哪条用例"，之后 observe() 记的观测都归它。"""
    global _current_nodeid
    _current_nodeid = nodeid


def observe(question, assistant_message, turn=1, conversation_id=None):
    """记一次问答的真实观测。由 ask 夹具在拿到响应后调用。

    assistant_message —— 响应里的 `data.assistantMessage`（dict）。
      只取我们关心的字段，**不存整个响应**：那些跟评测无关的东西存下来只会让 JSON 变噪音。
      但 `text` 存**全文** —— 它是"事后重新判分"的唯一原料（比如以后接了 LLM-as-Judge，
      要拿回答原文再跑一遍 judge，就不能只存长度）。
    """
    if _current_nodeid is None:
        return                      # 不在 pytest 上下文里（手工脚本等），静默跳过

    am = assistant_message or {}
    _observations.append({
        "nodeid": _current_nodeid,
        **_split_nodeid(_current_nodeid),
        "turn": turn,
        "question": question,
        "intent": am.get("intent"),
        "source": am.get("source"),
        "blocked": am.get("blocked"),
        "message_type": am.get("messageType"),
        "conversation_id": conversation_id,
        "text": am.get("text") or "",
        "text_len": len(am.get("text") or ""),
    })


def record_outcome(nodeid, outcome, duration=0.0, reason=""):
    """记一条用例的结果。由顶层 conftest 在 report 阶段调用。

    outcome 取值：passed / failed / xfailed / xpassed / skipped / error
      · xfailed —— 预期失败（已知缺陷，套件整体仍算绿）
      · xpassed —— strict xfail 却通过了（pytest 判它失败）—— 这是"该摘标记了"的信号
    评测报告要能**分开**统计这几类：把 xfail 混进 failed，会把"已知/待修"说成"回归"。
    """
    if any(o["nodeid"] == nodeid for o in _outcomes):
        return                      # 一条用例只记一次（call 阶段那次）
    _outcomes.append({
        "nodeid": nodeid,
        **_split_nodeid(nodeid),
        "outcome": outcome,
        "duration": round(duration, 2),
        "reason": (reason or "")[:300],
    })


def set_outcome_if_absent(nodeid, outcome, duration=0.0, reason=""):
    """只在该用例还没有结果时补记（给 setup / teardown 阶段的 error 用）。"""
    if any(o["nodeid"] == nodeid for o in _outcomes):
        return
    record_outcome(nodeid, outcome, duration, reason)


# ==================== 读取 / 落盘 ====================

def counts():
    """本次运行的两个关键计数（写日志时用）。"""
    model_calls = sum(1 for o in _observations if o["source"] != "blocked")
    blocked_calls = sum(1 for o in _observations if o["source"] == "blocked")
    return {
        "observations": len(_observations),
        "outcomes": len(_outcomes),
        "model_calls": model_calls,      # 真的递到模型的次数（= 花了钱的次数）
        "blocked_calls": blocked_calls,  # 被硬拦吃掉、没花钱的次数
    }


def has_data():
    return bool(_observations)


def build_payload(meta=None):
    """组装成待落盘的字典（也方便自测里直接用）。"""
    return {
        "meta": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **(meta or {}),
        },
        "stats": counts(),
        "outcomes": list(_outcomes),
        "observations": list(_observations),
    }


def dump(path=None, meta=None):
    """落盘。返回写入的路径；没有观测数据时**不写**并返回 None。"""
    if not has_data():
        return None
    out = Path(path) if path else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload(meta)
    # ensure_ascii=False：中文原文要能直接看；不加，报告里全是 \uXXXX 没法用
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = out.with_suffix(out.suffix + ".tmp")
    # 先写临时文件再替换：中途被打断也不会留下半截 JSON（评测数据丢了只能重跑，代价是钱）
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, out)
    return out


# ==================== 小工具 ====================

def _split_nodeid(nodeid):
    """`test_cases/ai_assistant/test_x.py::test_y[参数id]` 拆成四件套。

    为什么单独拆 `case_id`：参数化用例的 id 就是数据集里的 `name`，
    下游拿它去数据集里查"这条期望什么"，比按问题文本匹配可靠得多
    （数据集里确实存在同名问题，比如「你好」在意图集和拦截集里都出现）。
    """
    path, _, rest = nodeid.partition("::")
    func, _, param = rest.partition("[")
    case_id = param[:-1] if param.endswith("]") else param
    return {
        "file": os.path.basename(path),
        "test_func": func,
        "case_id": case_id,
    }
