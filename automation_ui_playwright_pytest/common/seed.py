# common/seed.py
# 作用：用例前置数据用**接口**造，不走 UI。
#
# 为什么不走 UI：
#   「编辑食谱」「删除食谱」这两条用例关心的是编辑生效、删除真删。
#   如果前置的"建"也走 UI，等于每条用例前面都挂着一段建流程 ——
#   建流程一坏，编辑/删除连带全红，看报告只知道"三条都挂了"，
#   分不清到底哪一步坏的。这叫测试耦合，是最常见的用例设计毛病。
#
#   前置走接口、被测动作走 UI，失败范围就被收窄到被测动作本身。
#   代价是"前置数据可能不符合 UI 的假设"，所以 payload 必须按前端
#   toRecipePayload 的合同来写（字段名、status=1、fit 是数组）——
#   合同不一致造出来的数据，UI 会当它不存在。

from common.cleanup import api


def seed_article(account, title, **overrides):
    """用接口发一篇文章，返回 id。

    存在的理由和 seed_recipe 一样，但这里还多一层：
      CI 的测试库是 `database/init_test_db.py`（schema + seed_test.sql）重建的，
      里面**没有任何业务文章**。任何"从知识列表里挑一条来点赞/评论"的用例
      在 CI 上都会因为列表为空而红 —— 而那不是产品坏了，是环境里没数据。
      正确做法不是给它加 skip，而是**用例自己造自己需要的那条数据**。
    """
    body = {
        "title": title,
        "summary": "自动化用例前置数据",
        "content": "这篇由自动化用例创建，用于验证文章互动（点赞）。\n正文第二段。",
        "category": "健康知识",
        "tags": "自动化",
        "author": "",
        "suitableFor": "",
        "goalType": "",
    }
    body.update(overrides)

    resp = api("POST", "/article/publish", account["token"], body)
    payload = resp.json() if resp.text else {}
    data = payload.get("data")
    aid = data.get("id") if isinstance(data, dict) else data
    assert resp.status_code < 400 and aid, (
        f"前置文章创建失败：HTTP {resp.status_code} {resp.text[:200]}"
    )
    return aid


def goal_restore_payload(snapshot):
    """把 GET /health/goal 的响应剪成"能安全 POST 回去"的 payload。

    为什么要剪：
      GET 返回的是**服务端视图**，里面有 id / userId / createTime / updateTime /
      status / proteinTarget 这些服务端自己算或自己管的字段。
      原样回灌的后果是"把服务端字段当用户输入提交" ——
      轻则被忽略，重则覆盖掉不该动的列，而且接口照样返回 200，
      清理"看起来成功了"。所以只回灌用户可写的那几项（白名单）。
    """
    if not isinstance(snapshot, dict):
        return None
    keep = (
        "goalType",
        "targetCalories",
        "proteinRatio",
        "carbsRatio",
        "fatRatio",
        "waterTarget",
        "targetWeight",
        "startDate",
        "endDate",
        "reminderEnabled",
        "reminderTime",
    )
    return {k: snapshot[k] for k in keep if k in snapshot}


def seed_recipe(account, name, **overrides):
    """用接口建一道自定义食谱，返回 id。

    payload 对齐 front2/src/services/adapters/recipe.js 的 toRecipePayload：
      · fit 必须是数组（后端存字符串，前端提交前 join）
      · ingredients 每项 {name, amount, unit}
      · status=1 才会出现在"我的食谱"列表里
    """
    body = {
        "name": name,
        "desc": "自动化前置数据",
        "mealType": "午餐",
        "cuisine": "中式",
        "level": "简单",
        "time": 15,
        "servings": 1,
        "kcal": 420,
        "p": 30,
        "c": 45,
        "f": 12,
        "fiber": 5,
        "fit": ["减脂"],
        "steps": ["前置数据：步骤一"],
        "tips": "",
        "status": 1,
        "ingredients": [{"name": "鸡胸肉", "amount": "100", "unit": "g"}],
    }
    body.update(overrides)

    resp = api("POST", "/recipe/save", account["token"], body)
    payload = resp.json() if resp.text else {}
    data = payload.get("data")
    rid = data.get("id") if isinstance(data, dict) else data
    assert resp.status_code < 400 and rid, (
        f"前置数据创建失败：HTTP {resp.status_code} {resp.text[:200]}"
    )
    return rid
