# -*- coding: utf-8 -*-
"""生成 / 打开 Allure 的 HTML 报告。

── 为什么需要这个脚本 ────────────────────────────────────────────
pytest 只负责产出**原始结果**（reports/allure-results/ 下一堆 JSON），
把它们渲染成能点的网页是另一件事，靠的是 Allure 官方的 **Java 命令行工具**
（allure-commandline）。于是每次都要手敲：

    allure generate reports/allure-results -o reports/allure-report --clean
    allure open reports/allure-report

两条命令、三个路径、还得记住 Java 装哪了。这个脚本把那堆细节收起来，
顺便解决三个实际麻烦：

  ① **找不到 allure 命令**：它默认不在 PATH 里。本脚本依次找
     --allure 参数 → 环境变量 ALLURE_CLI → PATH → 项目自带的 tools/allure-cli/，
     并检查 JAVA_HOME / java 是否可用，缺了会说清"缺什么、怎么补"。
  ② **跑测试和出报告是两件事，容易忘**：加 --run 就一条命令跑完用例再出报告，
     且**先清空旧结果**——不清的话上一轮的残留会混进这一轮的报告。
  ③ **工作目录**：不管你从哪个目录调用，它都按脚本位置算绝对路径。

── 用法 ──────────────────────────────────────────────────────────
    python tools/allure_report.py                    # 用上次 pytest 的结果生成报告
    python tools/allure_report.py --open             # 生成后启动本地服务并打开浏览器
    python tools/allure_report.py --run              # 先跑全套用例，再生成报告
    python tools/allure_report.py --run test_cases/auth -q     # 参数原样透给 pytest
    python tools/allure_report.py --serve            # 不落盘，直接起服务看结果（临时）
    python tools/allure_report.py --clean            # 只清空结果目录

⚠️ 跑之前先确认后端在跑（8080）—— 否则报告里会是一大片"环境问题"分类的红。
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
RESULTS = ROOT / "reports" / "allure-results"
REPORT = ROOT / "reports" / "allure-report"

# 本地自带的命令行工具（tools/allure-cli/allure-2.x.x/bin/...）
CLI_GLOB_PATTERNS = (
    "allure-cli/allure-*/bin/allure.bat",
    "allure-cli/allure-*/bin/allure",
    "allure-cli/bin/allure.bat",
    "allure-cli/bin/allure",
)

IS_WINDOWS = os.name == "nt"


def _say(message=""):
    print(message)


def find_allure_cli(explicit=None):
    """按优先级找一个能用的 allure 命令行工具，找不到返回 None。

    优先顺序刻意是"越靠外越优先"：
      --allure 参数 > 环境变量 > PATH > 项目自带。
      这样 CI 上想换一个统一版本，不用改代码、也不用删本地目录。
    """
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None

    env = os.environ.get("ALLURE_CLI")
    if env:
        path = Path(env)
        if path.exists():
            return path

    which = shutil.which("allure")
    if which:
        return Path(which)

    for pattern in CLI_GLOB_PATTERNS:
        # 目录名带版本号，倒序取最新的那个
        for candidate in sorted(TOOLS.glob(pattern), reverse=True):
            return candidate

    return None


def find_java():
    """allure 是个 Java 程序，没有 JRE 就启动不了。"""
    if os.environ.get("JAVA_HOME"):
        java = Path(os.environ["JAVA_HOME"]) / "bin" / ("java.exe" if IS_WINDOWS else "java")
        if java.exists():
            return java
    which = shutil.which("java")
    return Path(which) if which else None


def count_results(results_dir):
    """数一下结果目录里有多少份用例结果 —— 用来判断"生成出来的报告会不会是空的"。"""
    if not results_dir.exists():
        return 0
    return len(list(results_dir.glob("*-result.json")))


def clean_results(results_dir):
    if results_dir.exists():
        shutil.rmtree(results_dir)
        _say("已清空旧结果：%s" % results_dir)


def run_pytest(pytest_args, results_dir):
    """跑一轮用例，产出新的结果目录。

    用**当前解释器**跑（sys.executable），不写死 python 路径：
    谁调这个脚本，就用谁的环境（.venv / 系统 python 都行）。

    ⚠️ 这里**必须显式把 --alluredir 传给 pytest**，不能指望 conftest 的默认值。
       默认值是 `reports/allure-results`，而 `--results` 参数可能换成了别的目录
       （比如自检用的 tools/allure_selftest/_results）—— 结果写 A、脚本去 B 里找，
       就成了"报告是空的，但用例明明跑过了"。这个坑第一版就踩了。

    注意这里**不捕获输出**（capture_output=False）：
    用例跑起来时 conftest 的那套"用例分块"实时框要靠终端才好看，
    一旦重定向到管道，进度就全闷在缓冲里，跑十分钟你都看不到在干什么。
    """
    cmd = [sys.executable, "-m", "pytest", "--alluredir", str(results_dir)]

    # 如果用户在后面自己又给了 --alluredir，argparse 以最后一个为准，听他的。
    cmd += list(pytest_args or ["test_cases"])

    env = dict(os.environ)
    # Windows 下子进程默认按本地编码输出，中文用例名会变乱码。
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    _say("$ " + " ".join(cmd))
    _say("（cwd=%s）\n" % ROOT)
    started = time.time()
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env)
    _say("\n用例跑完：exit=%d，用时 %.0fs" % (proc.returncode, time.time() - started))
    return proc.returncode


def carry_history(results_dir, report_dir):
    """把上一份报告里的 history/ 搬进结果目录 —— **趋势图就靠这一步**。

    为什么得手工搬：allure 2.46 的 `generate` 见到目标目录已存在会直接拒绝
    （"Target directory ... is already in use, add a '--clean' option"），
    所以必须带 `--clean`；可 `--clean` 又把旧报告连同它的 history/ 一起删了。
    两头一夹，趋势就永远只剩本轮一根柱子。

    allure 的约定是：**结果目录里如果有一个 history/，就据此算出"跟前几轮比"**，
    并在新报告里产出新的 history/。所以正确顺序是：

        旧报告/history  →  复制到  结果目录/history  →  generate --clean  →  新报告/history

    实测（本项目）：不加这一步，Graphs 的 Trends 永远是 1 个点；
    加上之后连跑第二轮就能看到 2 个点。`--fresh` 会跳过它（想归零时用）。
    """
    source = report_dir / "history"
    if not source.is_dir():
        return False
    target = results_dir / "history"
    try:
        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, dirs_exist_ok=True)
        return True
    except OSError:
        return False


def generate(cli, results_dir, report_dir, fresh=False):
    """把原始结果渲染成静态 HTML 报告。

    `--clean` 是**必须的**（不是可选优化）：目标目录已存在时 allure 会直接报错退出。
    想保留趋势由 carry_history() 负责，别指望 "--clean 之外还有别的路"。
    """
    if not fresh and carry_history(results_dir, report_dir):
        _say("已接手上一轮 history（趋势图会接着画）")

    cmd = [str(cli), "generate", str(results_dir), "-o", str(report_dir), "--clean"]
    _say("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        _say("\n❌ 生成失败（exit=%d）。常见原因：Java 版本太低 / 结果目录里有坏文件。" % proc.returncode)
        return False
    return True


def serve(cli, target, port=4040):
    """起一个本地服务打开报告。

    为什么不直接双击 index.html：allure 的报告是**纯前端 + 一堆 JSON**，
    浏览器用 file:// 打开时读本地 JSON 会被同源策略拦住，页面一片空白。
    必须有个 http 服务（allure open 自带一个）才读得到数据。
    """
    _say("$ %s open %s -h 127.0.0.1 -p %d" % (cli, target, port))
    _say("服务起来后浏览器会自动打开；这个窗口关掉服务就停了。")
    subprocess.run([str(cli), "open", str(target), "-h", "127.0.0.1", "-p", str(port)],
                   cwd=str(ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="生成 / 打开 Allure HTML 报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="额外的未知参数会原样透给 pytest（配合 --run 使用），"
               "例如：python tools/allure_report.py --run test_cases/health -q",
    )
    parser.add_argument("--run", nargs="?", const="", default=None, metavar="目标",
                        help="先跑 pytest 再出报告（不写目标就是 test_cases 全套）")
    parser.add_argument("--open", action="store_true", help="生成后启动本地服务并打开浏览器")
    parser.add_argument("--serve", action="store_true", help="不生成静态报告，直接起服务看结果")
    parser.add_argument("--clean", action="store_true", help="只清空结果目录（不出报告）")
    parser.add_argument("--fresh", action="store_true", help="生成时连历史一起清掉（趋势图归零）")
    parser.add_argument("--results", default=str(RESULTS), help="结果目录（默认 reports/allure-results）")
    parser.add_argument("--report", default=str(REPORT), help="报告输出目录（默认 reports/allure-report）")
    parser.add_argument("--port", type=int, default=4040, help="--open / --serve 的端口（默认 4040）")
    parser.add_argument("--allure", default=None, help="手动指定 allure 命令行工具的路径")
    args, extras = parser.parse_known_args()

    results_dir = Path(args.results).resolve()
    report_dir = Path(args.report).resolve()

    # ---- ① 找工具链 ----
    cli = find_allure_cli(args.allure)
    java = find_java()
    if cli is None or java is None:
        _say("❌ 缺 Allure 命令行工具，没法生成 HTML 报告。")
        if java is None:
            _say("   · 没找到 Java：allure 是 Java 程序，需要 JRE 17+。")
            _say("     装一个（https://adoptium.net/）或设置 JAVA_HOME 后再来。")
        if cli is None:
            _say("   · 没找到 allure：把它下载解压到 tools/allure-cli/ 下即可，")
            _say("     或者设置环境变量 ALLURE_CLI 指向 bin/allure。")
            _say("     下载地址：https://github.com/allure-framework/allure2/releases")
            _say("     （也可以 pip 装好 allure-pytest 后，手动 `npm i -g allure-commandline`）")
        return 2
    _say("allure : %s" % cli)
    _say("java   : %s" % java)
    _say("")

    # ---- ② 只清目录 ----
    if args.clean and args.run is None:
        clean_results(results_dir)
        return 0

    # ---- ③ 先跑用例 ----
    if args.run is not None:
        # 跑用例要用 allure-pytest 才能产出结果；光有 Java 命令行工具不够。
        if importlib.util.find_spec("allure_pytest") is None:
            _say("❌ 没装 allure-pytest，跑用例不会产出任何结果。")
            _say("   .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
            return 2

        # 注意 "--run 后跟目标" 与 "目标作为未知参数" 两种写法都要支持：
        #   --run test_cases/auth   → args.run == "test_cases/auth"
        #   --run  （后面的参数被 parse_known_args 收进 extras）
        targets = [args.run] if args.run else []
        pytest_args = targets + extras
        # 结果目录必须**先清**：不清的话上一轮的残留会一起进报告，
        # 看起来像"这条用例跑了两遍"。
        clean_results(results_dir)
        run_pytest(pytest_args, results_dir)

    # ---- ④ 出报告 ----
    total = count_results(results_dir)
    if total == 0:
        _say("❌ 结果目录里没有结果：%s" % results_dir)
        _say("   是不是还没跑用例？先跑 `python -m pytest test_cases`，")
        _say("   或者用 `python tools/allure_report.py --run` 一条命令搞定。")
        return 1
    _say("结果文件：%d 份（%s）" % (total, results_dir))

    if args.serve:
        serve(cli, results_dir, port=args.port)
        return 0

    if not generate(cli, results_dir, report_dir, fresh=args.fresh):
        return 1
    _say("")
    _say("✅ 报告已生成：%s" % (report_dir / "index.html"))
    _say("   看报告：python tools/allure_report.py --open")
    _say("   （报告是纯静态页面，可以直接整个目录拷给别人 / 丢到 nginx 上）")

    if args.open:
        _say("")
        serve(cli, report_dir, port=args.port)
    return 0


if __name__ == "__main__":
    # Windows 控制台默认 GBK，中文提示会变乱码 —— 先把它掰成 utf-8。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
