# test_cases/ai_assistant/test_assistant_指标汇总.py
# 【任务：AI 助手 · 评测指标汇总（把数字放进 Allure 报告）】
# ══════════════════════════════════════════════════════════════════════════
# 这一条**不测业务**，只是把本轮 AI 用例跑出来的真实观测，汇总成两张附件贴进报告：
#   ·「AI助手 · 评测指标总览」—— 结论层：准确率 / 漏拦率 / 误拦率 / 攻破率 / 花了多少钱
#   ·「AI助手 · 评测指标明细」—— 证据层：混淆矩阵、判错清单、误拦清单、分桶明细
#
# ══ 数据从哪来：不重算，读同一份留痕 ══
#   指标口径只有一份 —— tools/eval/eval_runner.py 的 compute_metrics()，
#   和命令行导出 Markdown 时用的是**同一个函数**。这里不复制任何公式，
#   否则两边数字迟早对不上，而"两个地方数字不一样"比"只有一个地方有数字"更糟。
#
#   留痕来源：本模块 conftest.py 的 ask 夹具每次问答都调 eval_record.observe()，
#   数据攒在进程内存里；这里用 eval_record.build_payload() 取出**当前进程**的那一份。
#   不读 tools/eval/eval_results.json：那是上一轮磁盘上的结果（sessionfinish 才写），
#   单跑这一条时会读到陈旧数据。
#
# ══ 为什么它必须最后跑（且不能 assert）══
#   · 前面 10 条意图 / 20 条拦截 / 21 条越狱跑完，分母才齐；跑到一半汇总等于报半个数。
#     排序由 conftest.py 的 pytest_collection_modifyitems 保证（按文件挪到 AI 模块末尾）。
#   · 它**不断言业务结论**：指标是观测，不是门槛。把"准确率必须 100%"写进 pytest
#     等于让统计工具去判红绿 —— 小样本下它会随机红，最后没人再信红色。
#   · 因此它只在**自己拿不到数据**时失败（那说明埋点坏了），业务指标再差也不红。
#
# ⚠️ xdist（-n N）下：观测是进程内内存，worker 之间不合并。
#    这条用例只会看到自己所在 worker 的那一份 —— 数字不全，但不会错到误导（分母也小）。
#    要完整指标请串行跑。

import sys
from pathlib import Path

import pytest

from common import allure_helper, eval_record

# 工具脚本：按路径加进 sys.path 再 import（tools/ 无 __init__.py，按目录 import 不成立）
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools.eval.eval_runner import compute_metrics, render_allure   # noqa: E402

# 本用例**故意不要 `ask` 夹具**：
#   · 它不聊天、不花模型调用；
#   · `ask` 只有 function 级，拿它只为"初始化埋点"属于滥用夹具，而且会让这条用例
#     因为夹具的清理逻辑（删会话）而变慢、变脆。
#   埋点本身由前面那些真的调了 ask 的用例完成，数据已经在进程内存里。


def test_eval_metrics_summary():
    """本轮指标汇总 → 两张 Allure 附件。"""
    payload = eval_record.build_payload(meta={"scope": "本次 pytest 会话（进程内实测）"})
    obs_n = len(payload.get("observations", []))

    if obs_n == 0:
        # 不是业务失败，是"埋点/顺序"坏了：要么本用例被单独 -k 选中跑到了最前，
        # 要么这个 worker 没有观测。给出可执行的判断依据，而不是一句红。
        pytest.fail(
            "本次会话没有采到任何 AI 观测，汇总没有意义。\n"
            "  · 如果只跑了这一条（-k 指标汇总）：它必须排在 AI 模块最后才有数据；\n"
            "  · 如果用了 -n 并行：观测不跨 worker 合并，请串行跑；\n"
            "  · 如果前面所有 AI 用例都被 skip（AUTOTEST_REQUIRE_DB=0）：确实没有观测。",
            pytrace=False,
        )

    m = compute_metrics(payload)
    overview, detail = render_allure(m["intent"], m["guard"], m["jail"], m["run"])

    # 没装 allure / 本次不出报告时，这两行是空操作（allure_helper 内部降级），用例照样绿。
    allure_helper.attach_text("AI助手 · 评测指标总览", overview)
    allure_helper.attach_text("AI助手 · 评测指标明细", detail)

    # 只做一个"汇总本身没坏"的自检：总览里必须出现四个工位的关键词。
    # 这断的是**渲染管线**，不是业务指标 —— 业务数字好坏不影响结论。
    for keyword in ("意图识别", "输入安全", "红队", "模型调用"):
        assert keyword in overview, f"总览缺少「{keyword}」段落，汇总渲染可能坏了"
