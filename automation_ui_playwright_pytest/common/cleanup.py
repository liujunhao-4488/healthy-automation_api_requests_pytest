# common/cleanup.py
# 作用：用例产出的临时业务数据的清理。
#
# 为什么必须要有这个东西：
#   食谱、文章这两类用例会**真的往数据库里写数据**（不是 mock）。
#   不清理的话，每跑一次 weekly 就往测试库堆一批「UI自动化测试-173xxxx」，
#   跑一个月食谱库翻倍、知识列表全是废稿 —— 副作用比用例本身还大，
#   而且后面「搜索关键词」类用例会因为数据变多而变慢、变脆。
#
# 约定：**用例自己建的数据，用例自己删**。
#   删除走接口而不是走 UI：一是快（0.1s vs 点三下等动画），
#   二是稳（不依赖删除按钮的选择器，哪怕 UI 删不了也能兜底清理），
#   三是不占用例的断言位（清理失败不该让用例红，它只是环境卫生）。
#
# 实现上给一个 Cleanup 注册表，fixture 里 yield 出去、teardown 时倒序执行。
# 注册的是可调用对象而不是 id，这样「恢复原值」这种操作也能复用同一条通道。

import requests

from config.config import ADMIN_USER, BACKEND_URL

# 为什么用 Session 而不是 requests.request()：
#   trust_env（忽略环境代理）是 **Session 的属性**，不是单次请求的参数 ——
#   写成 requests.request(..., trust_env=False) 会直接 TypeError。
#   而本机配过环境代理，requests 默认走代理访问 127.0.0.1 会拿到 502，
#   所以必须显式关掉。复用一个 Session 顺带省掉每次重建连接池。
_session = requests.Session()
_session.trust_env = False


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def api(method, path, token, body=None, timeout=15):
    """直连后端的轻量封装（只给清理和造数据用，断言不靠它）。"""
    return _session.request(
        method,
        BACKEND_URL + path,
        json=body,
        headers=_headers(token),
        timeout=timeout,
    )


def delete(path, token):
    """删除接口。返回 (是否成功, 摘要)。失败不抛——清理失败不该让用例红。"""
    try:
        resp = api("DELETE", path, token)
        return resp.status_code < 400, f"{resp.status_code} {resp.text[:120]}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:120]


_admin_token = None


def admin_token():
    """管理员 token，只在清理文章时用。

    为什么必须换身份：
      /article/delete 是 @requireAdmin —— 普通用户**删不掉自己发布的文章**。
      这本身是个产品缺陷（UGC 没有撤回通道，发错只能等管理员），
      但它不影响清理：清理走管理员，和"用户能不能自删"是两件事。

    这里不走 auth_state.login_via_api：那个函数登录失败会自动注册，
    对管理员账号来说会把"密码错误"悄无声息地变成"建了个同邮箱的普通号"，
    然后清理永远 403，排查半天。管理员登录就该失败即报错。
    """
    global _admin_token
    if _admin_token:
        return _admin_token

    resp = _session.post(BACKEND_URL + "/auth/login", json=ADMIN_USER, timeout=15)
    body = resp.json() if resp.text else {}
    token = (body.get("data") or {}).get("token")
    if not token:
        raise RuntimeError(
            f"管理员登录失败（HTTP {resp.status_code}）：{resp.text[:120]}\n"
            f"  清理文章需要管理员权限（/article/delete 是 @requireAdmin）。"
            f"  检查 config.ADMIN_USER 的邮箱密码是否正确。"
        )
    _admin_token = token
    return _admin_token


def _unpublish_article(article_id, adm):
    """把文章下架（status=0）。

    为什么需要这个兜底：/article/delete 目前**删不掉** ——
    文章被评论 / 点赞 / 阅读历史外键引用，删除时直接
    SQLIntegrityConstraintViolation（后端没有先清子表也没有级联）。
    这是接口缺陷（见 README「已知缺陷」），但用例不能因为接口坏了就放任数据堆积，
    所以退一步：下架。下架后所有列表/搜索都看不到它，污染面归零。
    """
    resp = api("GET", f"/article/detail/{article_id}", adm)
    body = resp.json() if resp.text else {}
    art = body.get("data")
    if not isinstance(art, dict):
        return False, f"取不到文章详情，无法下架：{resp.text[:100]}"
    art["status"] = 0
    r = api("PUT", "/article/update", adm, art)
    ok = r.status_code < 400 and (r.json().get("code") == 200)
    return ok, ("已下架" if ok else f"下架失败 {r.status_code} {r.text[:100]}")


class Cleanup:
    """用例数据的清理注册表。

    用法：
        def test_xxx(user_page, cleanup):
            ...建了东西...
            cleanup.recipe(rid)          # 跑完删掉这道食谱
            cleanup.task(lambda: ...)    # 跑完做任意恢复动作

    为什么 teardown 里也要删（用例中途失败时）：
      失败的用例最容易留下残骸 —— 断言在「数据已建好」之后挂掉，
      用户下次打开食谱库就看到一条来路不明的「UI自动化测试」。
    """

    def __init__(self, token):
        self.token = token
        self._tasks = []

    def task(self, fn):
        """注册任意清理动作（恢复原值、解绑关系等）。"""
        self._tasks.append(fn)
        return self

    def restore(self, method, path, body, token=None):
        """注册一次"把值写回去"的接口动作，并**校验它真的成功了**。

        为什么恢复类不能直接用 task(lambda: api(...))：
          api() 返回的是 Response 对象，run() 里没法判断成功与否 ——
          失败会被静默吞掉。真踩过一次：PUT /user/profile 因异常没发出去，
          用户名就永久被改了名，而后面每次跑都把那个脏值当成"原值"。
          恢复类动作必须自带成功判据，失败就喊出来。
        """
        tok = token or self.token

        def _do():
            try:
                resp = api(method, path, tok, body)
                ok = resp.status_code < 400 and (
                    not resp.text or resp.json().get("code") == 200
                )
                return ok, f"{method} {path} → {resp.status_code} {resp.text[:100]}"
            except Exception as exc:  # noqa: BLE001
                return False, f"{method} {path} 异常：{str(exc)[:120]}"

        self._tasks.append(_do)
        return self

    def recipe(self, recipe_id):
        rid = recipe_id
        self._tasks.append(lambda: delete(f"/recipe/delete/{rid}", self.token))
        return self

    def article(self, article_id):
        aid = article_id

        def _del():
            try:
                adm = admin_token()
                ok, msg = delete(f"/article/delete/{aid}", adm)
                if ok:
                    return True, msg
                # 删除被外键挡住是**已知接口缺陷**，不是用例的问题 —— 自动降级为下架
                return _unpublish_article(aid, adm)
            except Exception as exc:  # noqa: BLE001
                return False, str(exc)[:160]

        self._tasks.append(_del)
        return self

    def run(self):
        """倒序执行（后建的先删，符合「依赖后进先出」）。"""
        results = []
        for fn in reversed(self._tasks):
            try:
                results.append(fn())
            except Exception as exc:  # noqa: BLE001
                results.append((False, str(exc)[:120]))
        self._tasks.clear()

        # 清理失败要在输出里喊一声：静默失败的结果就是测试库慢慢变脏，
        # 而人完全不知道（这正是"数据卫生"最容易烂掉的地方）。
        for res in results:
            if isinstance(res, tuple) and len(res) == 2 and res[0] is False:
                print(f"\n  ⚠️ 清理失败，可能留下测试数据：{res[1]}")
        return results
