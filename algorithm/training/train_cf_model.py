# -*- coding: utf-8 -*-
"""
协同过滤模型训练脚本 —— 使用 SVD 矩阵分解训练用户/食谱嵌入
======================================================================
核心流程：
  1. 从数据库（或种子数据）加载交互记录
  2. 构建 用户×食谱 的评分矩阵（稀疏矩阵，大部分位置为0）
  3. 均值中心化：每行减去该用户的平均评分，消除用户活跃度偏差
  4. 对中心化矩阵执行 SVD 奇异值分解 → 得到8维嵌入向量
  5. 保存嵌入字典到 cf_model.joblib

原理概述：
  矩阵分解是推荐系统的经典方法。它的核心思想是将一个大的、
  稀疏的用户×食谱评分矩阵 R (m×n) 分解为两个小矩阵的乘积：
    R ≈ U × V^T
  其中 U (m×k) 是用户嵌入矩阵，V (n×k) 是食谱嵌入矩阵，k 是嵌入维度。

  为什么不用深度学习而用 SVD？
    1. 数据量小（~7000条交互），深度学习容易过拟合
    2. SVD 可解释性强，答辩时可以说清每一步
    3. 训练速度快，适合冷启动和增量更新

  numpy.linalg.svd 实现比 sklearn TruncatedSVD 更底层，
  便于展示算法原理，且对稠密小矩阵效果相近。

SVD 数学原理（numpy_svd 算法）：
  对中心化矩阵 M 执行：M = U × Σ × V^T
  - U:  左奇异向量矩阵 (users × components)
  - Σ:  奇异值对角矩阵（按降序排列，反映每个维度的"重要性"）
  - V^T: 右奇异向量矩阵 (components × recipes)

  嵌入向量 = U × sqrt(Σ) （用户）和 V^T.T × sqrt(Σ) （食谱）
  为什么乘 sqrt(Σ)？
    这样 U×sqrt(Σ) 和 V×sqrt(Σ) 的点积就近似等于原始矩阵的
    中心化值： (U×sqrt(Σ)) · (V×sqrt(Σ)) = U×Σ×V^T = M
    相当于把奇异值的"信息量"均分给用户和食谱两边。

输入数据来源优先级：
  1. 优先：数据库（real_data_source.load_real_interactions）
  2. 回退：种子数据（RecommendEngine.user_recipe_data）

输出文件：cf_model.joblib（嵌入字典格式）
  {
    "user_embeddings": {"1": [0.12, -0.34, ...], ...},   # 181用户×8维
    "item_embeddings": {"5": [0.45, 0.23, ...], ...},    # 184食谱×8维
    "embedding_dim": 8,
    "algorithm": "numpy_svd",
    "data_source": "database" | "fallback_seed",
    "interaction_count": 6945,
    "user_count": 181,
    "recipe_count": 184
  }

命令行用法：
  python train_cf_model.py                          # 使用默认路径
  python train_cf_model.py --output ./custom.joblib  # 指定输出路径
  python train_cf_model.py --embedding-dim 16        # 指定嵌入维度
"""

import argparse
import os
import sys

import joblib
import numpy as np

# ── 路径处理：确保可以从 training/ 子目录导入 algorithm/ 下的模块 ──
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))     # training/ 目录
ALGORITHM_DIR = os.path.dirname(CURRENT_DIR)                 # algorithm/ 目录（上级）
if ALGORITHM_DIR not in sys.path:
    sys.path.insert(0, ALGORITHM_DIR)

from recommend_engine import RecommendEngine
from real_data_source import load_real_interactions


def train_cf_embeddings(output_path: str, embedding_dim: int = 8):
    """
    训练协同过滤嵌入的主函数。

    参数：
      output_path   : 模型输出路径（.joblib 文件）
      embedding_dim : SVD 嵌入维度，默认8维
                      维度越高能捕捉更多细节，但噪声也更多
                      8维是实践经验值：在181用户×184食谱的规模下，
                      8维已经能解释大部分方差，再多容易过拟合

    训练步骤（5步）：
      ① 加载交互数据
      ② 构建评分矩阵 + 建立ID索引映射
      ③ 均值中心化（消除用户活跃度偏差）
      ④ SVD 分解 + 提取嵌入向量
      ⑤ 序列化保存
    """

    # ═══════════════════════════════════════════════════════════
    # 步骤①：加载交互数据
    # ═══════════════════════════════════════════════════════════

    interactions = []        # 交互记录列表
    data_source = "database" # 数据来源标记（存入模型文件的 metadata）

    # 首选路径：从 MySQL 数据库加载真实交互数据
    try:
        interactions = load_real_interactions()
    except Exception:
        # 数据库不可用（连接失败 / PyMySQL未安装 / 表为空）→ 回退到种子数据
        interactions = []

    # 回退路径：数据库无数据时，使用 RecommendEngine 内置的种子交互数据
    if not interactions:
        engine = RecommendEngine()
        # engine.user_recipe_data 是 V1 引擎硬编码的8个用户×12道菜的模拟交互
        interactions = engine.user_recipe_data or []
        data_source = "fallback_seed"  # 标记数据来源，供 ModelRuntime 判断

    # 防御：如果两个来源都没数据，无法训练
    if not interactions:
        raise ValueError("No interaction data available for CF training")

    # ═══════════════════════════════════════════════════════════
    # 步骤②：构建评分矩阵
    # ═══════════════════════════════════════════════════════════

    # 提取所有不重复的用户ID和食谱ID，并排序（保证每次训练结果一致）
    user_ids = sorted({int(item["user_id"]) for item in interactions})
    recipe_ids = sorted({int(item["recipe_id"]) for item in interactions})

    # 建立 ID → 矩阵行/列索引 的映射表
    # 例如：用户ID 1 → 矩阵第0行，用户ID 5 → 矩阵第1行
    user_index = {user_id: idx for idx, user_id in enumerate(user_ids)}
    recipe_index = {recipe_id: idx for idx, recipe_id in enumerate(recipe_ids)}

    # 创建 m×n 的零矩阵（m = 用户数, n = 食谱数）
    # dtype=float 因为后面要做浮点运算
    matrix = np.zeros((len(user_ids), len(recipe_ids)), dtype=float)

    # 用交互数据填充矩阵：matrix[用户行][食谱列] = 评分值
    for row in interactions:
        user_id = int(row["user_id"])
        recipe_id = int(row["recipe_id"])
        rating = float(row.get("rating", 0.0))
        # 通过映射表找到矩阵坐标并填入评分
        matrix[user_index[user_id], recipe_index[recipe_id]] = rating

    # ═══════════════════════════════════════════════════════════
    # 步骤③：均值中心化（Mean Centering）
    # ═══════════════════════════════════════════════════════════

    # 计算每个用户的平均评分（只考虑有交互的项）
    # matrix.sum(axis=1) → 每个用户的总评分 → 除以该用户的交互数
    # np.maximum(..., 1) 防止除以0（无交互的用户平均分为0）
    user_means = np.where(
        matrix.sum(axis=1) > 0,
        matrix.sum(axis=1) / np.maximum((matrix > 0).sum(axis=1), 1),
        0
    )

    # 复制矩阵，逐行减去该用户的平均分
    centered_matrix = matrix.copy()
    for idx in range(centered_matrix.shape[0]):
        mask = centered_matrix[idx] > 0          # 只对有交互的位置减均值
        centered_matrix[idx, mask] -= user_means[idx]

    # 为什么要均值中心化？
    #   在隐式反馈系统中，用户活跃度差异大：
    #     - 活跃用户A 对很多菜有交互（收藏+记录），评分普遍偏高（3.5-5.0）
    #     - 不活跃用户B 只有少量交互，评分偏低（2.5-3.5）
    #   如果不做中心化，SVD 学到的会是"用户活跃度"而不是"用户口味"。
    #   中心化后，每个用户的评分变为"相对于自己平均分的偏差"：
    #     +1.2 → 比其他菜更喜欢这道
    #     -0.5 → 比其他菜更不喜欢这道
    #   这样 SVD 就能专注于学习口味偏好而非活跃度。

    # ═══════════════════════════════════════════════════════════
    # 步骤④：SVD 奇异值分解 → 提取嵌入向量
    # ═══════════════════════════════════════════════════════════

    # full_matrices=False → 经济型SVD（只计算前 min(m,n) 个奇异值）
    # 返回：U (m×k), Σ (k×k的对角线), V^T (k×n)
    u, singular_values, vt = np.linalg.svd(centered_matrix, full_matrices=False)

    # 实际使用的嵌入维度 = min(用户指定的维度, 奇异值总数)
    # 如果用户+食谱数 < 8，就用实际可用的最大维度
    components = max(1, min(int(embedding_dim), len(singular_values)))

    # 提取前 components 个奇异值并开方
    # np.maximum(..., 1e-6) → 防止极小奇异值导致数值不稳定
    sigma_sqrt = np.sqrt(np.maximum(singular_values[:components], 1e-6))

    # 计算用户嵌入 = U 的前 components 列 × sqrt(σ)
    # 形状：(用户数, components)
    user_embeddings = u[:, :components] * sigma_sqrt

    # 计算食谱嵌入 = V^T 的前 components 行 的转置 × sqrt(σ)
    # vt[:components, :].T 形状为 (食谱数, components)
    item_embeddings = vt[:components, :].T * sigma_sqrt

    # 为什么嵌入 = U×sqrt(Σ) 而不是 U×Σ？
    #   因为后续用余弦相似度来评估用户-食谱匹配程度：
    #     cos(u_i, v_j) = (u_i · v_j) / (|u_i| × |v_j|)
    #   如果用 U×Σ 和 V，点积 = U×Σ×V^T 能还原原始矩阵，但余弦相似度
    #   会被奇异值"扭曲"——大奇异值对应的维度会主导相似度计算。
    #   用 sqrt(Σ) 均分给两边，余弦相似度更均衡，推荐效果更稳定。

    # ═══════════════════════════════════════════════════════════
    # 步骤⑤：组装模型字典并保存
    # ═══════════════════════════════════════════════════════════

    # 构建标准化的模型字典格式
    model_payload = {
        # 用户嵌入：{"1": [0.12, -0.34, 0.56, ...], "2": [...], ...}
        # 键是字符串形式的用户ID，值是指定为list的8维浮点向量
        "user_embeddings": {
            str(user_ids[idx]): user_embeddings[idx].tolist()
            for idx in range(len(user_ids))
        },
        # 食谱嵌入：{"5": [0.45, 0.23, ...], "10": [...], ...}
        "item_embeddings": {
            str(recipe_ids[idx]): item_embeddings[idx].tolist()
            for idx in range(len(recipe_ids))
        },
        # ── 以下是元数据，供 ModelRuntime 判断模型状态 ──
        "embedding_dim": components,       # 实际使用的嵌入维度
        "algorithm": "numpy_svd",          # 算法标识
        "data_source": data_source,        # "database" 或 "fallback_seed"
        "interaction_count": len(interactions),  # 用于训练的交互总数
        "user_count": len(user_ids),       # 用户数量
        "recipe_count": len(recipe_ids)    # 食谱数量
    }

    # 确保输出目录存在，然后序列化保存
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model_payload, output_path)


def main():
    """命令行入口：解析参数 → 调用训练函数"""
    parser = argparse.ArgumentParser(
        description="训练 SVD 协同过滤嵌入模型"
    )
    parser.add_argument(
        "--output",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "models", "cf_model.joblib"
        ),
        help="模型输出路径（默认 algorithm/models/cf_model.joblib）"
    )
    parser.add_argument(
        "--embedding-dim", type=int, default=8,
        help="嵌入维度（默认8，建议范围 4-32）"
    )
    args = parser.parse_args()

    train_cf_embeddings(args.output, args.embedding_dim)


if __name__ == "__main__":
    main()
