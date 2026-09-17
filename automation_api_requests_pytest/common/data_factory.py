# common/data_factory.py
# 【数据工厂】用"代码"生成测试数据 —— 这才是真正"大量数据"的来源。
#
# 为什么？手写 1000 条数据是灾难；写 10 行生成逻辑，就能产出成千上万条数据，
# 而且**可复现**（固定随机种子 → 每次生成同一批 → 失败能重跑定位）。
#
# 类比：不去超市一条条挑菜，而是自己有个"菜园"，按需现摘。

import itertools
import random


def cartesian(**dimensions):
    """笛卡尔积：把各个维度的取值做"全组合"。

    cartesian(email=["A", "B"], password=["x", "y", "z"])
        → A×x, A×y, A×z, B×x, B×y, B×z  （共 2×3 = 6 条）
    """
    keys = list(dimensions)
    combos = itertools.product(*(dimensions[k] for k in keys))
    return [dict(zip(keys, c)) for c in combos]


def boundary_numbers(centers, span=1):
    """围绕"关键值"生成边界点：每个关键值取它自己以及前后 span 个。

    boundary_numbers([6, 50]) → [5, 6, 7, 49, 50, 51]
    （测试里的"边界值分析法"：错误往往就藏在边界上）
    """
    out = set()
    for c in centers:
        for d in range(-span, span + 1):
            v = c + d
            if v >= 0:
                out.add(v)
    return sorted(out)


def lengths(sizes):
    """把一组"长度数字"变成真实的字符串样本。

    lengths([0, 5, 6]) → ["", "aaaaa", "aaaaaa"]
    """
    return ["a" * n for n in sizes]


def fuzz_emails(n=10, seed=42):
    """批量"造"畸形邮箱（固定 seed → 结果可复现）。

    组成方式：从一个"畸形片段池"里轮着取，再拼上随机长度的尾巴，
    保证生成的都是"格式非法"的邮箱，用来验证接口稳定拒绝、不 500。
    """
    rng = random.Random(seed)
    fragments = [" ", "@", "@.", "..", "a@@b", "测试@", "<x>", "'; --", "a@b@c", "%00"]
    out = []
    for i in range(n):
        out.append(fragments[i % len(fragments)] + "x" * rng.randint(0, 5))
    return out
