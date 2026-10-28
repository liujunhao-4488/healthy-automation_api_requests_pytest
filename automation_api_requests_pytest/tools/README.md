# tools/ · 辅助脚本索引

`test_cases/` 产出红绿，用来守门；`tools/` 产出数字 / 清单 / 报告，用来做决策。
这里的东西**不参与断言**，跑挂了也不会让 CI 变红，所以别把"耗时不超过 3 秒"这类判据写成 assert 放进来。

```
tools/
├── run_tests.py            ← 主入口：跑 pytest，stdout/stderr 落到 logs/last_test_run.txt
├── reports/                ← 出报告（控制台表格 / Excel / Allure 网页）
├── eval/                   ← 评测：留痕、离线指标、LLM-as-Judge 校准
├── maintenance/            ← 维护清理
├── allure-cli/             ← 自带的 allure 命令行工具（约 32 MB，.gitignore 排除，不入库）
└── allure_selftest/        ← 故意做红的用例：只验 Allure 报告本身
```

## reports/ · 出报告

| 脚本 | 干什么 | 产物 |
|---|---|---|
| `reports/latency_report.py` | 拿提问集跑一遍，测每条回答要等多久（只有总耗时：接口是同步返回的） | `reports/assistant_latency_<时间>.xlsx` |
| `reports/jailbreak_report.py` | 拿对抗提问集跑一遍，按边界 / 手法算**攻破率**，打印命中词上下文 | `reports/jailbreak_<时间>.xlsx` |
| `reports/allure_report.py` | 把 `allure-results/` 渲染成能点的 HTML，`--run` 可顺手先跑一轮 | `reports/allure-report/index.html` |

```powershell
.venv\Scripts\python.exe tools/reports/latency_report.py --limit 5
.venv\Scripts\python.exe tools/reports/jailbreak_report.py --only 多轮
.venv\Scripts\python.exe tools/reports/allure_report.py --run --open
```

## eval/ · 评测

| 脚本 | 干什么 | 产物 |
|---|---|---|
| `run_tests.py` + `eval_record.py` | pytest 跑的时候把每次问答的真实观测留痕（旁路，不影响断言） | `eval/eval_results.json` |
| `eval/eval_runner.py` | 读留痕 JSON，离线算混淆矩阵 / 每类 P·R·F1 / 漏拦·误拦 / 分桶攻破率 | 控制台 + `--md` 指定的报告 |
| `eval/collect_judge_samples.py` | 采「问题 + 检索资料 + 回答」样本给人工盲标，**不含判断** | 项目根 `eval/judge_calibration/` |
| `eval/judge_faithfulness.py` | 用 judge prompt 逐条判 faithful / hallucinated，和人工标签算一致率 | 同上目录 |

```powershell
.venv\Scripts\python.exe tools/run_tests.py test_cases/ai_assistant -q   # 先跑一轮
.venv\Scripts\python.exe tools/eval/eval_runner.py                       # 再离线算指标
.venv\Scripts\python.exe tools/eval/judge_faithfulness.py                # 需要 DEEPSEEK_API_KEY
```

⚠️ `eval_results.json` 每次覆盖，且只认串行跑（并行 worker 之间不合并）。

## maintenance/ · 维护

| 脚本 | 干什么 |
|---|---|
| `maintenance/clean_artifacts.py` | 清 `logs/runs`（留 30 天）与 `reports/*.xlsx`（留 90 天）；默认演习，`--yes` 才真删 |

```powershell
.venv\Scripts\python.exe tools/maintenance/clean_artifacts.py          # 先看清单
.venv\Scripts\python.exe tools/maintenance/clean_artifacts.py --yes    # 真删
```

## 约定

- **日志落在 `logs/`**（`logs/last_test_run.txt`、`logs/last_cleanup.txt`），不再往 `tools/` 里堆临时文件；`_*.log` 这类一次性文件见一个删一个。
- 脚本按**自身位置**算项目根，所以在任何工作目录下调用都行；移动脚本时要同步改 `ROOT` 的层级（现在是 `parents[2]`）。
- 只用公开脚本名，不要再从 `tools/` 根目录直接 import 子目录脚本 —— 需要复用判据时按 `tools.reports.jailbreak_report` 这种完整路径 import。
