# test_cases/toolbox/test_data_loader.py
# 【任务：数据加载器本身】—— 测的是"工具"，不是"接口"。
#
# 为什么单独一个 toolbox/？因为它和别的用例不是一类东西：
#   别的文件是"拿工具去打接口"，这个文件是"验证工具自己对不对"。
#   它们失败的原因也完全不同：业务用例红了是后端的问题，
#   这里红了是**我们自己造的工具**坏了。
#
# 现在只管一件事：**Excel 多工作表**。
# "工作表名携带期望值"这套做法（加一批样本 = 加一张表，用例代码不用改）
# 全靠它撑着 —— 所以它坏了，上面那一层做得再漂亮也没用。
#
# 表在测试里**现造**（pytest 的 tmp_path 夹具），理由有两个：
#   ① 不往仓库里塞生成物 —— 生成物和生成逻辑放一起，早晚对不上；
#   ② 表长什么样，在这个文件里一眼能看全，不用去开 Excel。

import openpyxl
import pytest

from common.data_loader import ALL_SHEETS, SHEET_KEY, load_cases


@pytest.fixture
def excel(tmp_path):
    """造一个三张表的 xlsx，放进 tmp_path（pytest 每次跑给一个新的临时目录）。

    每张表的**表头故意不一样**（第二张少了 prompt 列）——
    多表拼起来时列能不能对齐，是这套东西最容易出错的地方。
    """
    wb = openpyxl.Workbook()
    wb.active.title = "替代类"
    wb.active.append(["name", "question", "intent"])
    wb.active.append(["替代-鸡胸肉", "鸡胸肉有什么替代品", "substitute"])
    wb.active.append(["替代-牛奶", "牛奶可以用什么代替", "substitute"])

    ws2 = wb.create_sheet("寒暄类")
    ws2.append(["name", "question"])          # ← 少一列，故意的
    ws2.append(["寒暄-你好", "你好"])

    ws3 = wb.create_sheet("空表")
    ws3.append(["name", "question"])          # 只有表头，没有数据行

    path = tmp_path / "cases.xlsx"
    wb.save(path)
    return path


def _load(excel, **kwargs):
    """借 load_cases 的读文件逻辑，但直接喂临时路径（它默认只认 data/ 目录）。

    做法：把 DATA_DIR 指到 tmp_path —— 不复制文件、不改 load_cases 的接口。
    """
    import common.data_loader as loader
    original = loader.DATA_DIR
    loader.DATA_DIR = excel.parent
    try:
        return load_cases(excel.name, **kwargs)
    finally:
        loader.DATA_DIR = original


def test_default_reads_active_sheet_only(excel):
    """不传 sheet → 只读活动表（老行为）。

    这条是**防回归**用的：加了多表能力之后，单表文件必须一个字都没变，
    否则现在跑着的那批用例（login_cases.xlsx）会悄悄多读到别的东西。
    """
    rows = _load(excel)

    assert [r["name"] for r in rows] == ["替代-鸡胸肉", "替代-牛奶"]
    assert SHEET_KEY not in rows[0], "老行为不该多出 _sheet 键"


def test_all_sheets_tags_each_row_with_sheet_name(excel):
    """sheet="*" → 三张表全读到，每行自带 `_sheet` 记着它来自哪张表。

    这是整套做法的地基：**期望值挂在表名上**，所以每行必须知道自己的表名。
    """
    rows = _load(excel, sheet=ALL_SHEETS)

    assert [r[SHEET_KEY] for r in rows] == ["替代类", "替代类", "寒暄类"], \
        f"表名或顺序不对：{[r[SHEET_KEY] for r in rows]}"
    assert [r["question"] for r in rows] == \
        ["鸡胸肉有什么替代品", "牛奶可以用什么代替", "你好"]


def test_all_sheets_keeps_header_differences_visible(excel):
    """两张表表头不一样时，各自缺的列**读成"没有这个键"**，不是 None、也不报错。

    为什么专门测这个：多表的常见错法是"拿第一张表的表头去套所有表"，
    那样第二张表的 question 会被错位读进来 —— 而且**读出来的数据看着还挺正常**，
    等到断言莫名其妙失败时才发现。这里钉住"缺列就是不出现"。
    """
    rows = _load(excel, sheet=ALL_SHEETS)
    greeting = [r for r in rows if r[SHEET_KEY] == "寒暄类"][0]

    assert greeting["question"] == "你好"
    assert "intent" not in greeting, "寒暄类那张表没有 intent 列，不该凭空多出来"


def test_empty_sheet_contributes_nothing(excel):
    """只有表头、没有数据行的表 → 一条都不贡献，也不报错。"""
    rows = _load(excel, sheet=ALL_SHEETS)

    assert not any(r[SHEET_KEY] == "空表" for r in rows), "空表不该产出任何行"
    assert len(rows) == 3, f"总数应为 3，实际 {len(rows)}"


def test_named_sheet_only_reads_that_sheet(excel):
    """sheet="寒暄类" → 只读那一张。"""
    rows = _load(excel, sheet="寒暄类")

    assert len(rows) == 1
    assert rows[0]["name"] == "寒暄-你好"


def test_missing_sheet_raises_with_sheet_list(excel):
    """表名写错 → 报错，并且**把实际有哪些表列出来**。

    为什么不静默返回空列表？因为"表名打错一个字母"和"这张表确实没数据"
    在结果上长得一样（都是空），但一个是笔误、一个是事实 —— 必须能分开。
    """
    with pytest.raises(ValueError) as exc:
        _load(excel, sheet="不存在的表")

    message = str(exc.value)
    assert "不存在的表" in message
    assert "替代类" in message, "报错里要带上实际存在的表名，方便一眼看出笔误"


def test_sheet_arg_on_non_excel_is_rejected():
    """给 .yaml 传 sheet → 直接报错，而不是"传了却静默无效"。

    yaml 那边根本没有表的概念，静默忽略等于骗人：
    调用方以为按表过滤了，实际上读到了全量数据。
    """
    with pytest.raises(ValueError) as exc:
        load_cases("assistant_意图识别_cases.yaml", sheet=ALL_SHEETS)

    assert "只对 .xlsx 有意义" in str(exc.value)
