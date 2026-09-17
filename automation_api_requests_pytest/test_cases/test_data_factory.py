# test_cases/test_data_factory.py
# 【任务 #3.6：数据工厂 —— 用代码"生成"数据】
#
# 与外部文件（JSON/CSV/YAML/Excel）的区别：
#   文件适合"精选的少量代表数据"（人维护）；
#   工厂适合"大批量、有规律、可复现"的数据（代码维护）。
#
# 关键词：**可复现**。固定 seed → 每次生成同一批数据 → 挂了能重跑定位。

import pytest

from common.data_factory import boundary_numbers, cartesian, fuzz_emails, lengths
from config import TEST_USER

VALID_EMAIL = TEST_USER["email"]


# ---------- 1) 组合生成：非法邮箱 × 非法密码，全覆盖 ----------
INVALID_EMAILS = ["", "bad-email", "a" * 200 + "@qq.com"]
INVALID_PWDS = ["", "wrong_pwd"]
COMBOS = cartesian(email=INVALID_EMAILS, password=INVALID_PWDS)


@pytest.mark.parametrize(
    "case",
    COMBOS,
    ids=[f"{i:02d}-{c['email'][:8] or '空邮箱'}-{c['password'] or '空密码'}" for i, c in enumerate(COMBOS)],
)
def test_login_invalid_combinations(api, case):
    """2 维 × (3,2) 个取值 = 6 种组合，一次跑完，全部必须被拒。"""
    resp = api.post("/auth/login", json=case)
    assert resp.status_code == 400, f"非法组合应被拒，实际 HTTP {resp.status_code}"
    assert resp.json()["code"] == 400


# ---------- 2) 边界值生成：围绕关键长度取"边界 ±1" ----------
PWD_OF_LENGTH = lengths(boundary_numbers([0, 1, 64, 256], span=1))


@pytest.mark.parametrize("pwd", PWD_OF_LENGTH, ids=[f"len={len(p)}" for p in PWD_OF_LENGTH])
def test_login_password_length_boundaries(api, pwd):
    """边界值法：只跑"边界点"，用极少数据覆盖大量场景。

    说明：登录接口本身不校验密码长度（长度规则在注册接口），
          这里用各种"长度奇特"的密码验证系统一律稳稳拒绝、不崩。
    """
    resp = api.post("/auth/login", json={"email": VALID_EMAIL, "password": pwd})
    assert resp.status_code == 400
    assert resp.json()["code"] == 400


# ---------- 3) 批量 fuzz：一次生成一打畸形输入 ----------
FUZZ = fuzz_emails(n=12, seed=42)


@pytest.mark.parametrize("email", FUZZ, ids=[f"{i:02d}-{e[:6].strip() or '空白'}" for i, e in enumerate(FUZZ)])
def test_login_fuzz_emails(api, email):
    """12 条畸形邮箱由"工厂"生成，非手写；断言只关心'被拒绝，不 500'。"""
    resp = api.post("/auth/login", json={"email": email, "password": "123456"})
    assert resp.status_code == 400, f"[{email!r}] 应被拒绝，实际 HTTP {resp.status_code}"
    assert resp.json()["code"] == 400
