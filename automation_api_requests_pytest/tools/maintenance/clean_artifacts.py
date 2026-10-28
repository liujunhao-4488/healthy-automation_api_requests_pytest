# -*- coding: utf-8 -*-
"""清理测试产物：logs/runs/ 与 reports/ 里的旧文件。
【工具】给"每跑一次就多一个"的目录补一个上限。

── 为什么需要它 ──────────────────────────────────────────────
有两处产物是"一次运行一个文件"，**天生没有上限**：

    logs/runs/run-<时间>.log          ← logger.py 的 begin_run_log()
    reports/<类型>_<时间>.xlsx        ← latency_report.py / jailbreak_report.py

它们的设计初衷是对的（一次一个，便于回溯，互不覆盖），代价是没有上限：
跑得越多，文件越多。体积其实很小（百来 KB），真正难受的是**翻不着**——
半年后 runs/ 里躺着几百个 run-*.log，你就再也找不到"上周那条红是什么时候开始的"。

对照：logs/latest.log 每次覆盖、logs/autotest.log 用 RotatingFileHandler(1MB×3)，
这两个**已经自我约束**了，本脚本不碰它们（它们也不在 logs/runs/ 里，天然安全）。

── 用法（在项目根目录下跑）────────────────────────────────────
    python tools/maintenance/clean_artifacts.py                     # 演习：只列清单，不删
    python tools/maintenance/clean_artifacts.py --runs-days 7       # 换个保留天数
    python tools/maintenance/clean_artifacts.py --yes               # 真删

默认保留：logs/runs 最近 30 天，reports 最近 90 天。
（报告是用来回溯决策的，该留得久一点；运行日志过了几天就没参考价值了。）

⚠️ 默认是**演习**（dry-run）。不加 --yes 绝不删东西——先看清单，再决定。

── 三道护栏（这类脚本最容易翻车的地方）──────────────────────
① 只匹配**严格命名**（run-*.log / assistant_latency_*.xlsx / jailbreak_*.xlsx），
   绝不写 *.log、* 这种宽通配——通配写宽了，删的就不是你想删的。
② reports/ 里**认不出的文件一律不动**，只列出来提示你（见 UNKNOWN 段）。
   将来多一种报告类型，它会先在这里出现，而不是被静默删掉。
③ 每个目录**至少保留最新 1 个**（KEEP_AT_LEAST）——
   防止"很久没跑测试 → 所有文件都超过天数 → 全删光"。
"""
import argparse
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # 项目根（tools/maintenance/ 往上两级）

RUNS_DIR = ROOT / "logs" / "runs"
REPORT_DIR = ROOT / "reports"

# 演习/真删的清单写到 logs/last_cleanup.txt（logs/ 已被 .gitignore 排除）。
# 这台机器跨 shell 抓不到 stdout，所以让脚本自己写文件、再打开看。
AUDIT = ROOT / "logs" / "last_cleanup.txt"

# reports/ 里认得出类型的报告命名（前缀_时间戳.xlsx）。
# 新增报告类型时，把前缀加到这里，否则它会落进"未识别、不删"那一档。
REPORT_PATTERNS = [
    "assistant_latency_*.xlsx",
    "jailbreak_*.xlsx",
]

# 每个目录至少保留最新几个——哪怕它们全都超过保留天数了。
KEEP_AT_LEAST = 1


def plan(label, dirpath, patterns, days):
    """算一个目录里哪些该删。**只读，不删**——删的动作留给 main()。

    按修改时间（mtime）而不是文件名里的时间戳来判新旧：
    mtime 是文件系统记的，一定真实；文件名可以被人手动改。
    """
    if not dirpath.is_dir():
        return {"label": label, "days": days, "dir": dirpath,
                "missing": True, "delete": [], "keep": [], "unknown": []}

    matched, unknown = [], []
    for p in sorted(dirpath.iterdir()):
        if not p.is_file():          # 目录绝不碰
            continue
        if any(p.match(pat) for pat in patterns):
            matched.append(p)
        else:
            unknown.append(p)

    # 新的排前面：先保住最新的 KEEP_AT_LEAST 个，再对剩下的按天数砍。
    matched.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    cutoff = time.time() - days * 86400

    delete = [p for i, p in enumerate(matched)
              if i >= KEEP_AT_LEAST and p.stat().st_mtime < cutoff]
    delete_set = set(delete)
    keep = [p for p in matched if p not in delete_set]

    return {"label": label, "days": days, "dir": dirpath, "missing": False,
            "delete": delete, "keep": keep, "unknown": unknown}


def render(plans, dry_run):
    """把清单整理成文本（既打印也写文件）。"""
    now = time.time()
    header = "【演习 dry-run】只列清单，不删" if dry_run else "【真删】已执行删除"
    out = [header, ""]
    total, total_bytes = 0, 0

    for pl in plans:
        out.append("=" * 56)
        out.append("[%s]  保留最近 %d 天" % (pl["label"], pl["days"]))
        if pl["missing"]:
            out.append("  （目录不存在，跳过）")
            continue

        if pl["delete"]:
            out.append("  ── 待删（%d 个）──" % len(pl["delete"]))
            for p in pl["delete"]:
                age = (now - p.stat().st_mtime) / 86400
                out.append("    - %-42s %5.1f 天前" % (p.name, age))
        else:
            out.append("  ── 无需删除 ──")
        out.append("  ── 保留 %d 个 ──" % len(pl["keep"]))

        if pl["unknown"]:
            out.append("  ── 未识别命名，不动（%d 个）──" % len(pl["unknown"]))
            for p in pl["unknown"]:
                out.append("    ? %s" % p.name)

        total += len(pl["delete"])
        total_bytes += sum(p.stat().st_size for p in pl["delete"])
        out.append("")

    out.append("=" * 56)
    if dry_run:
        out.append("合计：将删除 %d 个文件，共 %.1f KB" % (total, total_bytes / 1024))
        out.append("确认无误后加 --yes 才会真删。")
    else:
        out.append("合计：已删除 %d 个文件，释放 %.1f KB" % (total, total_bytes / 1024))
    return "\n".join(out), total


def main():
    ap = argparse.ArgumentParser(description="清理 logs/runs 与 reports 的旧文件")
    ap.add_argument("--runs-days", type=int, default=30,
                    help="logs/runs 保留多少天（默认 30）")
    ap.add_argument("--reports-days", type=int, default=90,
                    help="reports 保留多少天（默认 90）")
    ap.add_argument("--yes", action="store_true",
                    help="真删。不加时只演习、只列清单")
    args = ap.parse_args()

    plans = [
        plan("logs/runs", RUNS_DIR, ["run-*.log"], args.runs_days),
        plan("reports", REPORT_DIR, REPORT_PATTERNS, args.reports_days),
    ]

    dry_run = not args.yes
    text, total = render(plans, dry_run)

    if args.yes:                              # 先渲染（含每个文件的大小），再动手删
        for pl in plans:
            for p in pl["delete"]:
                p.unlink()

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(text, encoding="utf-8")
    print(text)
    print("\n[clean_artifacts] %s，%d 个文件；清单见 %s"
          % ("演习完成" if dry_run else "清理完成", total, AUDIT))


if __name__ == "__main__":
    # Windows 控制台默认不是 UTF-8，中文可能乱码 —— 不崩就行（文件里是好的）。
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    main()
