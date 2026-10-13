# -*- coding: utf-8 -*-
"""跑 pytest，并把 stdout / stderr 统统写进一个文件。

── 为什么需要它 ──────────────────────────────────────────────
这台机器跨 shell **拿不到 stdout**（Bash 不可用，PowerShell 也能吞掉子进程输出）。
于是"跑个测试看看结果"变成一件很别扭的事：命令回显是空的，exit code 又不可信。

办法就是：让 pytest 的输出落到一个文件里，再用 Read 打开看。
原来每次都要手搓一个临时 runner，跑完还得删；现在固定成这一个文件，反复用。

── 用法 ──────────────────────────────────────────────────────
    python tools/run_tests.py                         # 默认跑 AI 助手目录
    python tools/run_tests.py test_cases/health -q    # 参数原样透给 pytest
    python tools/run_tests.py -k 词表外 -v

输出写到 tools/_last_test_run.txt（覆盖式），命令结束时会打印一行摘要。

⚠️ 跑之前先确认后端在跑（8080）—— 否则会看到一片 ConnectionError。
"""
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(__file__).resolve().parent / "_last_test_run.txt"

# 不带参数时给个默认目标 —— 就是本项目最常跑的那个目录。
args = sys.argv[1:] or ["test_cases/ai_assistant", "-q"]

# 用**当前解释器**跑 pytest，不写死 python 路径：
# 谁调用这个脚本，就用谁的环境（managed python / 项目 .venv 都行）。
cmd = [sys.executable, "-m", "pytest"] + args

# Windows 下子进程默认按本地编码输出，中文用例名会变乱码。
# 这两个环境变量强制它走 utf-8（PYTHONUTF8 管解释器，PYTHONIOENCODING 管管道）。
env = dict(os.environ)
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

t0 = time.time()
proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, env=env)
elapsed = time.time() - t0

text = (
    "$ " + " ".join(cmd) + "\n"
    + "(cwd=%s)\n\n" % ROOT
    + proc.stdout.decode("utf-8", "replace")
    + "\n----- stderr -----\n"
    + proc.stderr.decode("utf-8", "replace")
)

OUT.write_text(text, encoding="utf-8")

print("wrote %s (%d chars, %.1fs, exit=%d)" % (OUT, len(text), elapsed, proc.returncode))
