# test_cases/record/test_record_增删查.py
# 【A 档 · 核心写链路 + 数据归属】饮食记录：提交 → 列表 → 详情 → 删除
#
# ============ 为什么它是"必须覆盖"里最该补的一个 ============
# 覆盖矩阵上它原来整块是 ⬜（6 个接口 0 条用例）。而它是整个系统的**数据源头**：
# 摄入趋势、饮食建议、AI 助手回答"我今天吃了多少"，全都读 diet_record。
# 写错了不会报错，只会让后面所有数字静默地不对 —— 这类缺陷最难被发现。
#
# 它满足 A 档的两条判断标准：
#   ② 数据归属边界 —— detail/{id} 和 DELETE/{id} 的入参只有 id；
#   ③ 确定性业务规则 —— 总热量/总蛋白是**明细求和**，期望值能算死（116+165=281）。
#     这是本项目里少数"不用调模型、结果完全可预测"的接口，性价比最高。
#
# ============ 这个文件的分组 ============
#   一、写 → 读 闭环
#   二、汇总计算（确定性规则，最值钱的几条）
#   三、日期筛选
#   四、删除语义（软删 / 二次删除）
#   五、越权（IDOR）
#   六、鉴权
#   七、已知缺陷（xfail 钉住）
#
# ⚠️ 所有请求体都通过 conftest 的 `submit_record` 夹具走**接口**提交，
#    不直插库 —— 因为这里要测的正是"接口有没有把数据写对"。

import pytest

from common import db

pytestmark = pytest.mark.requires_db


# ==================== 小工具 ====================

def _records(api, who, **kwargs):
    """读某人的记录列表（裸数组）。"""
    body = api.assert_ok(
        api.record.list_records(headers=who["headers"], **kwargs),
        f"用户 {who['userId']} 读取记录列表应成功",
    )
    return body.get("data") or []


def _find(records, record_id):
    return next((r for r in records if r["id"] == record_id), None)


def _two_dish_details():
    """两条明细，用来验汇总。数字取自 API.md 7.1 和食材库实测值：

        米饭   100g → 116 kcal / 蛋白 2.6 / 碳水 25.6 / 脂肪 0.3
        鸡胸肉 100g → 165 kcal / 蛋白 31  / 碳水 0    / 脂肪 3.6
        合计         → 281 kcal / 蛋白 33.6 / 碳水 25.6 / 脂肪 3.9
    """
    return [
        {"foodName": "米饭", "amount": 100, "unit": "g",
         "calories": 116, "protein": 2.6, "carbs": 25.6, "fat": 0.3},
        {"foodName": "鸡胸肉", "amount": 100, "unit": "g",
         "calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    ]


# ==================== 一、写 → 读 闭环 ====================

def test_submitted_record_appears_in_list(api, record_user, submit_record):
    """提交之后，列表里必须**立刻**能查到，且关键字段原样回来。

    ══ 字段逐个断，而不是"查到了就算过" ══
    后端在"存"和"读"之间做了一次字段映射（请求里叫 amount，库里叫 quantity；
    请求里叫 date，响应里叫 recordDate）。映射错位不会有任何报错，
    表现是"记录存在但日期全是今天""用量全是 0"。
    只断 id 在不在，这类错误一辈子看不见。
    """
    rid = submit_record(record_user, date="2026-11-03", meal_type="lunch",
                        notes="闭环测试", details=_two_dish_details())

    item = _find(_records(api, record_user), rid)
    assert item is not None, f"刚提交的 id={rid} 在列表里查不到"

    assert item["recordDate"].startswith("2026-11-03"), (
        f"提交的日期是 2026-11-03，读回来是 {item['recordDate']} —— 日期映射错了"
    )
    assert item["mealType"] == "lunch", f"餐次读回来是 {item['mealType']!r}"
    assert item["notes"] == "闭环测试", f"备注读回来是 {item['notes']!r}"
    assert item["isDeleted"] == 0, "新提交的记录 isDeleted 应该是 0"
    assert item["details"] is not None and len(item["details"]) == 2, (
        f"列表里这条记录应该带 2 条明细，实际 {item.get('details')}"
    )


def test_detail_returns_details_of_the_record(api, record_user, submit_record):
    """detail 接口返回的是**明细数组**，不是整条记录。

    ══ 这条用例的一半价值是"把接口的真实形状写下来" ══
    方法叫 detail、名字像"记录详情"，实际 data 是 diet_record_detail 的行列表：
        [{"recordId":..., "foodName":"米饭", "quantity":100.0, ...}]
    记录本身的字段（日期、餐次、总热量）在 /record/list 里。
    不知道这一点的人会写 data["recordDate"] 然后 KeyError，还以为是接口坏了。

    ══ 另一半价值：amount → quantity 的改名 ══
    提交时字段叫 amount，读回来叫 quantity。这条断言把映射关系钉住。
    """
    rid = submit_record(record_user, details=_two_dish_details())

    body = api.assert_ok(
        api.record.detail(rid, headers=record_user["headers"]),
        "读取记录详情应成功",
    )
    details = body["data"]
    assert isinstance(details, list), (
        f"detail 的 data 应该是明细数组，实际是 {type(details).__name__}：{str(details)[:200]}"
    )
    assert len(details) == 2, f"应该有 2 条明细，实际 {len(details)}"

    names = [d["foodName"] for d in details]
    assert names == ["米饭", "鸡胸肉"], f"明细顺序/内容不对：{names}"

    rice = details[0]
    assert rice["quantity"] == 100.0, (
        f"提交时 amount=100，读回来 quantity={rice['quantity']} —— amount→quantity 映射错了"
    )
    assert rice["unit"] == "g", f"单位读回来是 {rice['unit']!r}"
    assert all(d["recordId"] == rid for d in details), "明细的 recordId 没指回这条记录"


# ==================== 二、汇总计算（确定性规则）====================

def test_totals_are_summed_from_details(api, record_user, submit_record):
    """总热量/总蛋白必须是明细求和 —— 这是本项目最"纯"的一条断言。

    ══ 为什么这条最值钱 ══
    A 档判断标准第 3 条：「确定性业务规则，期望值能写死」。
    116 + 165 = 281 是天经地义的，不需要问任何人"应该多少"。
    而它一旦算错，首页的今日摄入、趋势图、AI 的回答**全部跟着错**，
    并且没有任何一处会报错。

    ══ 只断热量是不够的 ══
    四个汇总字段各走各的累加语句（totalCalories / totalProtein / ...），
    复制粘贴时把 totalCarbs 写成 += fat 是很典型的手滑。
    所以四个都断。
    """
    rid = submit_record(record_user, details=_two_dish_details())

    item = _find(_records(api, record_user), rid)
    assert item is not None, "刚提交的记录没出现在列表里"

    assert item["totalCalories"] == pytest.approx(281.0), (
        f"总热量应为 116+165=281，实际 {item['totalCalories']}"
    )
    assert item["totalProtein"] == pytest.approx(33.6), (
        f"总蛋白应为 2.6+31=33.6，实际 {item['totalProtein']}"
    )
    assert item["totalCarbs"] == pytest.approx(25.6), (
        f"总碳水应为 25.6+0，实际 {item['totalCarbs']}"
    )
    assert item["totalFat"] == pytest.approx(3.9), (
        f"总脂肪应为 0.3+3.6=3.9，实际 {item['totalFat']}"
    )


def test_totals_persisted_to_db_match_response(api, record_user, submit_record):
    """接口返回的汇总值，和库里存的值必须一致。

    ══ 为什么要查库，不是"接口自洽就行" ══
    total 字段在库里是**单独存的列**，不是每次查询时现算。
    如果后端只在响应里算了一遍、没写进表（或者写了个错的），
    接口看是对的，但趋势分析、导出报表读的是库里的列 —— 那里是错的。
    接口自洽 ≠ 数据正确，这条补的就是那个缺口。
    """
    rid = submit_record(record_user, details=_two_dish_details())

    row = db.query(
        "SELECT total_calories, total_protein, total_carbs, total_fat "
        "FROM diet_record WHERE id = %s", (rid,), one=True,
    )
    assert row is not None, f"接口返回提交成功，但库里查不到 id={rid}"
    assert row["total_calories"] == pytest.approx(281.0), (
        f"库里 total_calories={row['total_calories']}，接口算的是 281 —— 落库和响应不一致"
    )
    assert row["total_protein"] == pytest.approx(33.6)


# ==================== 三、日期筛选 ====================

def test_date_range_filter_narrows_results(api, record_user, submit_record):
    """startDate / endDate 必须真的过滤（实测生效）。

    ══ 为什么专门测这个 ══
    同一个 /record/list 上，**分页参数完全无效、日期参数完全有效**（实测）。
    两者在代码里长得几乎一样（都是 query param），很容易被当成"都不生效"
    或"都生效"。分别钉住，才能在看板/报表出问题时知道该怀疑哪一半。
    """
    submit_record(record_user, date="2026-09-01")
    submit_record(record_user, date="2026-09-15")
    submit_record(record_user, date="2026-10-01")

    got = _records(api, record_user, page_size=50,
                   start_date="2026-09-10", end_date="2026-09-30")
    dates = sorted(r["recordDate"][:10] for r in got)
    assert dates == ["2026-09-15"], (
        f"筛 2026-09-10 ~ 2026-09-30 应该只剩 09-15，实际 {dates}"
    )


def test_reversed_date_range_returns_empty_not_error(api, record_user, submit_record):
    """开始日期晚于结束日期 → 返回空列表，不报错。

    ══ 为什么期望"空列表"而不是"400" ══
    这是**查询**接口，参数本身语法合法（都是合法日期），只是选不出数据。
    health/goal 那种"结束日期不能早于开始日期"是**写入**校验（存进去就是坏数据）；
    查询条件反了只是查不到东西。两者不该混为一谈。
    这条钉的是"别哪天有人加了一个 400 校验把前端搞崩"。
    """
    submit_record(record_user, date="2026-09-15")

    got = _records(api, record_user, page_size=50,
                   start_date="2026-09-30", end_date="2026-09-10")
    assert got == [], f"反向日期区间应该返回空列表，实际返回 {len(got)} 条"


# ==================== 四、删除语义 ====================

def test_delete_then_gone_from_list_and_detail(api, record_user, submit_record):
    """删除之后，列表和详情都必须查不到，且库里是**软删**。

    ══ 软删这件事要靠库来确认 ══
    接口层面"查不到了"有两种实现：真删行，或者置 is_deleted=1。
    两者对用户看起来一样，但对**统计**影响完全不同：
    如果趋势分析那条 SQL 忘了加 `is_deleted = 0`，删掉的记录还会算进摄入总量。
    所以这里既断"接口查不到"，也断"库里那行还在、只是标了 1"，
    把实际采用的方案写进用例 —— 以后谁改成硬删，这条会红，提醒他去查统计口径。
    """
    rid = submit_record(record_user)

    api.assert_ok(api.record.delete_record(rid, headers=record_user["headers"]),
                  "删除记录应成功")

    assert _find(_records(api, record_user, page_size=100), rid) is None, (
        "删除后列表里还有这条记录"
    )
    detail = api.record.detail(rid, headers=record_user["headers"])
    api.assert_error(detail, 400, "记录不存在或无权限查看")

    row = db.query("SELECT is_deleted FROM diet_record WHERE id = %s", (rid,), one=True)
    assert row is not None, (
        f"删除后库里这一行**没了**（硬删）。实测是软删（is_deleted=1），"
        f"如果确实改成硬删，请同步检查趋势统计的 SQL 是否还带 is_deleted 过滤。"
    )
    assert row["is_deleted"] == 1, f"删除后 is_deleted 应该是 1，实际 {row['is_deleted']}"


def test_delete_twice_returns_business_error(api, record_user, submit_record):
    """重复删除 → 业务 400「记录不存在或无权限删除」，不是 500，也不是 200。

    ══ 为什么这条要和"收藏接口幂等"对比着看 ══
    收藏是幂等的（重复取消也 200），删除**不是**。这不是不一致，是取舍不同：
      · 收藏是**可反复点的开关**，双击很常见 → 幂等更友好；
      · 删除是**不可逆操作**，第二次点应该明确告诉用户"已经没了"，
        静默返回成功会让人误以为"刚才那下没生效"。
    这个差异是真实的产品决策，用例把它写下来，免得后来的人"顺手统一"。
    """
    rid = submit_record(record_user)
    api.assert_ok(api.record.delete_record(rid, headers=record_user["headers"]), "第一次删除应成功")

    resp = api.record.delete_record(rid, headers=record_user["headers"])
    api.assert_error(resp, 400, "记录不存在或无权限删除")


# ==================== 五、越权（IDOR）====================

def test_intruder_cannot_read_others_record(api, record_pair, submit_record):
    """B 拿 A 的记录 id 查详情 → 400，且**文案与"记录不存在"完全一致**。

    ══ 防枚举：为什么文案必须一样 ══
    如果越权返回"无权查看"、不存在的 id 返回"记录不存在"，
    攻击者就有了一个探针：遍历 id 就能知道全站哪些记录存在。
    实测两者是同一句「记录不存在或无权限查看」（和通知模块同一套设计）。
    这条断言就是在钉这个约定。
    """
    owner, intruder = record_pair["owner"], record_pair["intruder"]
    rid = submit_record(owner, notes="A 的私密记录")

    resp = api.record.detail(rid, headers=intruder["headers"])
    api.assert_error(resp, 400, "记录不存在或无权限查看")

    # 对照：真的不存在的 id 必须给出**同一句**文案
    missing = api.record.detail(999999999, headers=intruder["headers"])
    api.assert_error(missing, 400, "记录不存在或无权限查看")

    assert resp.json()["message"] == missing.json()["message"], (
        "「别人的记录」和「不存在的记录」文案不一致 —— 攻击者可以据此判断 id 是否存在"
    )


def test_intruder_cannot_delete_others_record(api, record_pair, submit_record):
    """B 删 A 的记录 → 被拒，而且 A 的记录**必须还在**。

    ══ 只看状态码会漏掉"先删后验权" ══
    后端完全可能先执行 DELETE、再判断归属（或者事务回滚失败），
    响应照样是 400。所以这里用 A 自己的接口回查一遍 ——
    查库也行，但走接口能保证读的是同一个后端、同一个库。
    """
    owner, intruder = record_pair["owner"], record_pair["intruder"]
    rid = submit_record(owner, notes="A 的记录，B 不该能删")

    resp = api.record.delete_record(rid, headers=intruder["headers"])
    api.assert_error(resp, 400, "记录不存在或无权限删除")

    still = _find(_records(api, owner, page_size=100), rid)
    assert still is not None, (
        f"B 删 A 的记录被 400 拒绝了，但 A 的记录真的没了（id={rid}）—— "
        f"先删后验权，或者归属校验压根没生效。"
    )
    assert still["isDeleted"] == 0, "A 的记录被越权请求标记成已删除了"


def test_intruder_list_excludes_others_records(api, record_pair, submit_record):
    """B 的列表里不能出现 A 的记录。"""
    owner, intruder = record_pair["owner"], record_pair["intruder"]
    rid = submit_record(owner)

    ids = {r["id"] for r in _records(api, intruder, page_size=100)}
    assert rid not in ids, (
        f"B 的列表里出现了 A 的记录 id={rid} —— 列表 SQL 没按 user_id 过滤，是数据泄漏。"
    )


# ==================== 六、鉴权 ====================

def test_list_requires_token(api):
    """列表不带 token → 401。

    ⚠️ 401 的响应体**有内容**（2026-11-06 实测全站统一）：
           {"code":401,"message":"登录已过期，请重新登录","data":null}
       覆盖矩阵里"401 空响应体"的旧记录已过时 —— 现在能正常断文案。
    """
    resp = api.record.list_records(headers=None)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)


def test_submit_requires_token(api, record_user, submit_record):
    """提交不带 token → 401，且不能真的写进库。"""
    # 先造一条，拿到一个真实存在的 userId 做对照（未登录时不该新增任何行）
    before = len(_records(api, record_user, page_size=100))

    resp = api.record.submit(
        {"date": "2026-11-06", "mealType": "breakfast",
         "details": [{"foodName": "偷渡", "amount": 1, "unit": "g", "calories": 1}]},
        headers=None,
    )
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)

    after = len(_records(api, record_user, page_size=100))
    assert after == before, "未登录的提交被 401 拒绝了，但记录数变了 —— 先写库后验权"


# ==================== 七、已知缺陷（xfail 钉住）====================

@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #17：/record/list 的 page/pageSize 完全不生效，传 pageSize=2 仍返回全部",
)
def test_bug_page_size_is_ignored(api, record_user, submit_record):
    """分页参数无效 —— API.md 7.2 明确写的是「分页获取饮食记录」。

    ══ 依据（为什么算缺陷而不是"设计如此"）══
    API.md 7.2 的示例请求就是 `?page=1&pageSize=10`，说明**接口设计上是要分页的**。
    实测 page=1/page=2/pageSize=2 三种组合返回**完全相同**的全量数据，
    说明参数被收了但没用上（或者 SQL 里漏了 LIMIT）。

    ══ 真实影响 ══
    记录会随使用天数线性增长（一天 3~4 餐）。前端按分页写的话，
    第一页就会把用户几年的记录一次性拉下来 —— 响应体越来越大，
    到某一天变成超时。这是个**会随时间恶化**的缺陷，不是"多点流量而已"。
    """
    for i in range(5):
        submit_record(record_user, date=f"2026-07-{10 + i:02d}")

    page1 = _records(api, record_user, page=1, page_size=2)
    assert len(page1) <= 2, (
        f"pageSize=2 却返回了 {len(page1)} 条 —— 分页参数没生效（缺陷 #17）"
    )


@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #14：提交记录缺 mealType 时，400 响应体吐出 SQL 异常原文"
           "（Field 'meal_type' doesn't have a default value + INSERT 语句 + mapper 类名）",
)
def test_bug_missing_meal_type_leaks_sql(api, record_user):
    """缺必填字段 → 期望「餐次不能为空」，实际吐 SQL 异常。

    ══ 依据 ══
    meal_type 在库里是 NOT NULL，接口层就该用 @NotBlank 拦住并给用户提示。
    现在是一路走到数据库才炸，然后把 MyBatis 的异常原文当 message 返回 ——
    里面带着表名、列名、mapper 全限定类名。
    这与已修复的缺陷 #3（height=0 吐 MySQL 异常栈）是**同一类问题**，
    说明"参数校验靠数据库兜底"这个习惯还没纠过来。
    """
    resp = api.record.submit({"date": "2026-11-06", "details": []},
                             headers=record_user["headers"])

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    message = resp.json().get("message") or ""
    assert "SQL" not in message and "meal_type" not in message, (
        f"响应体泄露了 SQL / 列名：\n{message[:400]}"
    )
    assert "餐次" in message, f"期望一句用户能看懂的提示，实际：{message[:300]}"


@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #15：mealType 无枚举白名单，任意字符串（如 'xxx'）都能入库",
)
def test_bug_invalid_meal_type_accepted(api, record_user):
    """非法 mealType 被接受 —— 与已修复的缺陷 #8（gender 三套取值并存）同源。

    ══ 依据 ══
    库表注释写死了取值范围：`餐次: breakfast/lunch/dinner/snack`。
    注释就是设计意图。实测传 "xxx" 返回 200 并原样入库。

    ══ 影响 ══
    前端按 mealType 分组显示三餐（早餐/午餐/晚餐/加餐），"xxx" 会落进
    一个没有任何分组能接住的地方 —— 用户提交成功了，但记录在页面上"消失"。
    这种"存进去了、看不见"的 bug 用户只会反馈"我的记录丢了"。
    """
    resp = api.record.submit(
        {"date": "2026-11-06", "mealType": "xxx", "details": []},
        headers=record_user["headers"],
    )

    assert resp.status_code == 400, (
        f"非法餐次 'xxx' 被接受了（HTTP {resp.status_code}），库表注释限定的取值是 "
        f"breakfast/lunch/dinner/snack"
    )


@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #18：明细里的 calories / amount 允许负数，总热量可以变成 -500",
)
def test_bug_negative_calories_accepted(api, record_user, submit_record):
    """负热量能被提交 —— 与已修复的缺陷 #4（age=-1 等数值无范围校验）同源。

    ══ 依据 ══
    缺陷 #4 的处置是"给 HealthInfoDTO 补 @Min/@DecimalMin"，说明团队
    已经确立的标准是「数值字段要有范围校验」，而不是"后端不校验、前端拦住就行"。
    这里是同一个系统里的另一个 DTO，标准应当一致（团队先例，判定纪律第 3 条）。

    ══ 影响 ══
    负值不是"多一条脏数据"那么简单：它是**求和项**。
    一条 -500 kcal 的记录会让当天摄入总量凭空少 500，
    用户看到"今天才吃了 300 大卡"然后继续吃 —— 这个产品的核心价值就没了。
    """
    rid = submit_record(record_user, details=[
        {"foodName": "负热量", "amount": -100, "unit": "g", "calories": -500}
    ])

    item = _find(_records(api, record_user), rid)
    assert item is not None
    assert item["totalCalories"] >= 0, (
        f"总热量被算成了 {item['totalCalories']} —— 负数明细被无条件接纳并参与求和"
    )


# ==================== 八、观察点（不断言，只记录）====================
# 这两条**故意不写成断言**，因为"应该怎样"还没有依据（判定纪律：先确认再定性）。
# 写成用例的唯一目的是把行为记录下来，以后有人问"同一天两顿早餐会怎样"，
# 不用重新试一遍。

def test_same_day_same_meal_appends_rather_than_overwrites(api, record_user, submit_record):
    """同一天同一餐次提交两次 = 两条独立记录（不是覆盖）。

    ⚠️ 这是**观察点，不是缺陷** —— API.md 没有规定"一天一餐只能有一条"，
       前端也可能是"再加一道菜"的交互。所以这里只断言"确实是两条"，
       把这个事实固定下来。如果产品后来决定要合并，改这条用例即是新期望。
    """
    first = submit_record(record_user, date="2026-08-01", meal_type="breakfast")
    second = submit_record(record_user, date="2026-08-01", meal_type="breakfast")

    assert first != second, "两次提交返回了同一个 id，说明是覆盖而不是追加"

    same_day = [r for r in _records(api, record_user, page_size=100)
                if r["recordDate"][:10] == "2026-08-01"]
    assert len(same_day) == 2, (
        f"同一天同一餐次提交两次，实际有 {len(same_day)} 条记录。"
        f"如果后端改成合并（upsert），请同步更新这条用例的期望值。"
    )


def test_submit_without_details_is_accepted_with_zero_totals(api, record_user):
    """不带 details 也能提交成功，各汇总值都是 0。

    ⚠️ **观察点，不断言为缺陷**：空记录在业务上未必错
       （用户可能只想记一句"今天没好好吃饭"）。
       这里记录的是"后端确实允许"，以及"汇总值是 0 而不是 null"——
       后者会影响到前端算平均值时会不会 NaN。
    """
    body = api.assert_ok(
        api.record.submit({"date": "2026-11-06", "mealType": "dinner"},
                          headers=record_user["headers"]),
        "不带 details 的提交当前会被接受",
    )
    data = body["data"]
    assert data["totalCalories"] == 0.0, (
        f"空明细时 totalCalories 应该是 0.0（不是 null），实际 {data['totalCalories']!r}"
    )
