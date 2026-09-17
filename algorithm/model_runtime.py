# -*- coding: utf-8 -*-
"""
模型运行时 —— 管理 ML 模型的加载、缓存刷新与推理调用
======================================================================
职责：
  1. 负责所有模型文件的加载（SVD嵌入、GBDT回归器、特征定义）
  2. 启动时自动检测模型是否基于数据库训练，不是则重新训练
  3. 提供两个打分入口：score_cf（协同过滤） 和 score_nutrition_ml（营养匹配）
  4. 封装了所有 ML 推理细节，engine 层不需要感知模型格式

类：ModelRuntime（单例，由 RecommendEngineV2 持有）

模型文件（存于 models/ 目录）：
  cf_model.joblib      → SVD 嵌入字典 {user_embeddings, item_embeddings, metadata}
  nutrition_model.joblib → sklearn GradientBoostingRegressor 对象
  feature_schema.json   → 33维特征顺序 + 默认值字典

三种 CF 推理路径（score_cf 内部按优先级尝试）：
  路径1(当前使用): dict 模式 → 余弦相似度 + Sigmoid校准
  路径2(备用):    predict_score 方法 → surprise 库模型
  路径3(备用):    predict 方法 → 通用回归模型（构建8维特征向量）
"""

import json
import math
import os
from typing import Any, Dict, Iterable, List, Optional

import joblib


class ModelRuntime:
    """统一的模型管理类，封装加载、刷新、推理全流程"""

    def __init__(self, models_dir: Optional[str] = None):
        # 默认模型目录：algorithm/models/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = models_dir or os.path.join(base_dir, "models")

        # 三个模型资源，启动时加载
        self.cf_model = None           # 协同过滤模型（dict 或 sklearn 对象）
        self.nutrition_model = None    # GBDT 营养匹配模型
        self.feature_schema = None     # 33维特征定义

        self._load_assets()

    # =========================================================================
    # 模型加载与自动重训
    # =========================================================================

    def _load_assets(self):
        """
        加载所有模型文件。
        加载顺序：cf_model → nutrition_model → feature_schema
        加载后立即检查是否需要自动重训（数据来源标记检查）
        """
        self.cf_model = self._safe_load_joblib("cf_model.joblib")
        self.nutrition_model = self._safe_load_joblib("nutrition_model.joblib")
        self.feature_schema = self._safe_load_json("feature_schema.json")

        # 检查模型是否基于数据库训练，如果不是则触发自动重训
        if self._should_refresh_real_data_assets():
            self._refresh_real_data_assets()
            # 重训后重新加载新模型
            self.cf_model = self._safe_load_joblib("cf_model.joblib")
            self.nutrition_model = self._safe_load_joblib("nutrition_model.joblib")
            self.feature_schema = self._safe_load_json("feature_schema.json")

    def _should_refresh_real_data_assets(self) -> bool:
        """
        判断是否需要重新训练模型。

        条件（三个同时满足才跳过重训）：
          1. 环境变量 RECOMMEND_REAL_DATA_TRAINING 不是 0/false/off/no
          2. cf_model 的 data_source 标记为 "database"
          3. feature_schema 的 data_source 标记为 "database"
          4. nutrition_model 存在（不是 None）

        任何一个不满足 → 需要重训。
        设计意图：数据库有数据时自动基于数据库训练，没有则保留现有模型。
        """
        # 检查环境变量：是否显式禁用了重训
        mode = str(os.getenv("RECOMMEND_REAL_DATA_TRAINING", "1")).strip().lower()
        if mode in {"0", "false", "off", "no"}:
            return False

        # 检查 CF 模型的数据来源标记
        cf_is_database = isinstance(self.cf_model, dict) and self.cf_model.get("data_source") == "database"
        # 检查特征 schema 的数据来源标记
        nutrition_is_database = isinstance(self.feature_schema, dict) and self.feature_schema.get("data_source") == "database"

        # 三个条件都满足才不需要重训
        return not (cf_is_database and nutrition_is_database and self.nutrition_model is not None)

    def _refresh_real_data_assets(self):
        """
        调用训练脚本重新训练所有模型。
        训练脚本内部优先使用数据库数据，数据库不可用时回退到种子数据。
        新模型直接覆盖 models/ 目录下的旧文件。
        """
        try:
            from training.train_cf_model import train_cf_embeddings
            from training.train_nutrition_model import train_nutrition_model

            cf_model_path = os.path.join(self.models_dir, "cf_model.joblib")
            nutrition_model_path = os.path.join(self.models_dir, "nutrition_model.joblib")
            feature_schema_path = os.path.join(self.models_dir, "feature_schema.json")

            os.makedirs(self.models_dir, exist_ok=True)
            # 训练 SVD 协同过滤嵌入
            train_cf_embeddings(cf_model_path)
            # 训练 GBDT 营养匹配模型
            train_nutrition_model(nutrition_model_path, feature_schema_path)
        except Exception:
            # 训练失败不阻塞服务启动 — 继续使用现有模型或种子数据
            return

    # =========================================================================
    # 安全的文件加载
    # =========================================================================

    def _safe_load_joblib(self, filename: str):
        """安全加载 joblib 文件，文件不存在或加载失败返回 None"""
        path = os.path.join(self.models_dir, filename)
        if not os.path.exists(path):
            return None
        try:
            return joblib.load(path)
        except Exception:
            return None

    def _safe_load_json(self, filename: str):
        """安全加载 JSON 文件，文件不存在或解析失败返回 None"""
        path = os.path.join(self.models_dir, filename)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return None

    # =========================================================================
    # 协同过滤打分（CF Score）
    # =========================================================================

    def score_cf(
        self,
        user_id: Any,
        recipe_id: Any,
        user_profile: Optional[Dict[str, Any]] = None,
        recipe_features: Optional[Dict[str, float]] = None,
        fallback_score: Optional[float] = None
    ) -> Optional[float]:
        """
        协同过滤打分的主入口，返回 1.0 ~ 5.0 的评分。


           cf_model 是 dict → _score_cf_from_embedding_dict()
           从嵌入字典取用户/食谱的8维向量，算余弦相似度 + Sigmoid校准
           当前生产环境走这条路径。

        """
        if self.cf_model is None:
            # 模型文件不存在，直接回退
            return fallback_score

        try:
            # ── 路径1：嵌入字典模式（当前生产环境走这里）──
            if isinstance(self.cf_model, dict):
                score = self._score_cf_from_embedding_dict(user_id, recipe_id)
                if score is not None:
                    return self._clamp(score, 1.0, 5.0)

            # ── 路径2：surprise 库模型（有 predict_score 方法）──
            if hasattr(self.cf_model, "predict_score"):
                raw = self.cf_model.predict_score(user_id, recipe_id)
                return self._normalize_rating(raw)

            # ── 路径3：通用 regression 模型（只有 predict 方法）──
            if hasattr(self.cf_model, "predict"):
                vector = self._build_cf_predict_vector(
                    user_id, recipe_id, user_profile, recipe_features
                )
                prediction = self.cf_model.predict([vector])
                raw = prediction[0] if isinstance(prediction, Iterable) else prediction
                return self._normalize_rating(raw)
        except Exception:
            return fallback_score

        return fallback_score

    # =========================================================================
    # 营养匹配 ML 打分（Nutrition ML Score）
    # =========================================================================

    def score_nutrition_ml(
        self,
        feature_map: Dict[str, float],
        fallback_score: Optional[float] = None
    ) -> Optional[float]:
        """
        GBDT 营养匹配打分，返回 0.0 ~ 5.0 的评分。

        推理流程：
          1. 按 feature_schema.json 定义的顺序构建33维特征向量
          2. 调用 GradientBoostingRegressor.predict() 得到预测值
          3. 归一化到 0-5 分

        如果模型是分类器（有 predict_proba 方法），则用正类概率×5作为分数。
        当前 GBDT 是回归器（有 predict 方法），走 predict 路径。

        模型不可用时返回 fallback_score（调用方传入的规则护栏分）。
        """
        if self.nutrition_model is None:
            return fallback_score

        try:
            # 按 feature_schema 定义的特征顺序构建数值向量
            vector = self._build_feature_vector(feature_map)

            # 分类器路径（备用，当前不走）
            if hasattr(self.nutrition_model, "predict_proba"):
                probabilities = self.nutrition_model.predict_proba([vector])[0]
                positive_prob = float(probabilities[-1]) if len(probabilities) > 0 else 0.5
                return self._clamp(positive_prob * 5.0, 0.0, 5.0)

            # 回归器路径（当前 GBDT 走这里）
            if hasattr(self.nutrition_model, "predict"):
                prediction = self.nutrition_model.predict([vector])
                raw = prediction[0] if isinstance(prediction, Iterable) else prediction
                return self._normalize_zero_to_five(raw)
        except Exception:
            return fallback_score

        return fallback_score

    # =========================================================================
    # CF 模型推理辅助方法
    # =========================================================================

    def _build_cf_predict_vector(
        self,
        user_id: Any,
        recipe_id: Any,
        user_profile: Optional[Dict[str, Any]],
        recipe_features: Optional[Dict[str, float]]
    ) -> List[float]:
        """
        为路径3（通用 predict 模型）构建8维特征向量：
        [userId, recipeId, age, bmi, calories, protein, carbs, fat]
        """
        user_profile = user_profile or {}
        recipe_features = recipe_features or {}

        return [
            self._safe_float(user_id),
            self._safe_float(recipe_id),
            self._safe_float(user_profile.get("age", 0)),
            self._safe_float(user_profile.get("bmi", 0)),
            self._safe_float(recipe_features.get("calories", 0)),
            self._safe_float(recipe_features.get("protein", 0)),
            self._safe_float(recipe_features.get("carbs", 0)),
            self._safe_float(recipe_features.get("fat", 0))
        ]

    def _score_cf_from_embedding_dict(self, user_id: Any, recipe_id: Any) -> Optional[float]:
        """
        路径1的核心实现：从嵌入字典中取出8维向量，计算余弦相似度，
        然后用 Sigmoid 校准到 1-5 分的合理评分区间。

        步骤：
          1. 从 cf_model["user_embeddings"][str(user_id)] 取用户8维向量
          2. 从 cf_model["item_embeddings"][str(recipe_id)] 取食谱8维向量
          3. 点积 / (||user_vec|| × ||item_vec||) = 余弦相似度 [-1, 1]
          4. Sigmoid校准: 1.0 + 4.0 × sigmoid(cosine × 3.0) → [1, 5]

        为什么乘3.0后再Sigmoid？
          原始的余弦相似度在 [-1, 1] 范围，大部分值集中在 [-0.3, 0.7]。
          乘以3.0把值拉开到 [-3, 3]，让 sigmoid 函数在更敏感的区域工作，
          输出有更好的区分度。

        用户/食谱不在嵌入字典中 → 返回 None（冷启动场景）。
        """
        # 校验 cf_model 结构：必须是包含 user_embeddings 和 item_embeddings 的字典
        user_embeddings = self.cf_model.get("user_embeddings") if isinstance(self.cf_model, dict) else None
        item_embeddings = self.cf_model.get("item_embeddings") if isinstance(self.cf_model, dict) else None
        if not isinstance(user_embeddings, dict) or not isinstance(item_embeddings, dict):
            return None

        # 查找用户和食谱对应的嵌入向量
        user_key = str(user_id)
        recipe_key = str(recipe_id)
        user_vec = user_embeddings.get(user_key)
        item_vec = item_embeddings.get(recipe_key)
        if user_vec is None or item_vec is None:
            # 冷用户或冷食谱，返回 None → 调用方使用 fallback
            return None

        # 计算余弦相似度 = (u·v) / (|u| × |v|)
        numerator = 0.0    # 点积: Σ(user_i × item_i)
        user_norm = 0.0    # 用户向量 L2 范数平方
        item_norm = 0.0    # 食谱向量 L2 范数平方
        for left, right in zip(user_vec, item_vec):
            left_value = self._safe_float(left)
            right_value = self._safe_float(right)
            numerator += left_value * right_value
            user_norm += left_value * left_value
            item_norm += right_value * right_value

        if user_norm <= 0 or item_norm <= 0:
            return None

        cosine = numerator / (math.sqrt(user_norm) * math.sqrt(item_norm))

        # Sigmoid 校准：将 [-1, 1] 的余弦值映射到 [1, 5] 的评分区间
        # sigmoid(cosine × 3.0) → (0, 1) → 再 ×4 + 1 → [1, 5]
        calibrated = 1.0 + 4.0 * self._sigmoid(cosine * 3.0)
        return calibrated

    # =========================================================================
    # 营养 ML 模型推理辅助方法
    # =========================================================================

    def _build_feature_vector(self, feature_map: Dict[str, float]) -> List[float]:
        """
        按 feature_schema 定义的特征顺序构建推理用的特征向量。
        缺失的特征用 schema 中的默认值（0.0）填充。
        feature_schema 不完整时，按字典键排序作为退化方案。
        """
        feature_order = self._resolve_feature_order(feature_map)
        defaults = self._resolve_feature_defaults()
        return [
            self._safe_float(feature_map.get(name, defaults.get(name, 0.0)))
            for name in feature_order
        ]

    def _resolve_feature_order(self, feature_map: Dict[str, float]) -> List[str]:
        """
        解析特征顺序。优先级：
          1. schema["feature_order"]
          2. schema["nutrition_features"]
          3. schema["features"]
          4. 退化：按 feature_map 的键排序
        """
        schema = self.feature_schema
        if isinstance(schema, dict):
            for key in ("feature_order", "nutrition_features", "features"):
                value = schema.get(key)
                if isinstance(value, list) and value:
                    return [str(item) for item in value]

        if isinstance(schema, list) and schema:
            return [str(item) for item in schema]

        return sorted(feature_map.keys())

    def _resolve_feature_defaults(self) -> Dict[str, float]:
        """解析特征默认值（来自 feature_schema.json 的 defaults 字段）"""
        if isinstance(self.feature_schema, dict):
            defaults = self.feature_schema.get("defaults")
            if isinstance(defaults, dict):
                return {str(key): self._safe_float(value) for key, value in defaults.items()}
        return {}

    # =========================================================================
    # 评分归一化
    # =========================================================================

    def _normalize_rating(self, raw_score: Any) -> float:
        """
        将各种可能的原始评分归一化到 1.0 ~ 5.0。
        自动识别三种常见的评分范围：
          [0, 1]   → 映射到 [1, 5]  (概率)
          [0, 5]   → 直接使用        (5分制)
          [0, 100] → 除以20          (百分制)
      """
        numeric = self._safe_float(raw_score)
        if 0.0 <= numeric <= 1.0:
            return self._clamp(1.0 + numeric * 4.0, 1.0, 5.0)
        if 0.0 <= numeric <= 5.0:
            return self._clamp(numeric, 1.0, 5.0)
        if 0.0 <= numeric <= 100.0:
            return self._clamp(numeric / 20.0, 1.0, 5.0)
        return self._clamp(3.2, 1.0, 5.0)  # 无法识别时的中性分

    def _normalize_zero_to_five(self, raw_score: Any) -> float:
        """
        类似于 _normalize_rating，但范围是 0.0 ~ 5.0（用于营养ML分）。
        营养ML分允许0分（完全不适合），CF分最低1分。
        """
        numeric = self._safe_float(raw_score)
        if 0.0 <= numeric <= 1.0:
            return self._clamp(numeric * 5.0, 0.0, 5.0)
        if 0.0 <= numeric <= 5.0:
            return self._clamp(numeric, 0.0, 5.0)
        if 0.0 <= numeric <= 100.0:
            return self._clamp(numeric / 20.0, 0.0, 5.0)
        return self._clamp(3.2, 0.0, 5.0)

    # =========================================================================
    # 基础数学工具
    # =========================================================================

    def _safe_float(self, value: Any) -> float:
        """安全浮点转换，防 None/非数字/异常"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _sigmoid(self, value: float) -> float:
        """
        Sigmoid 激活函数：将任意实数映射到 (0, 1) 区间。
        S 型曲线，中心在 x=0 时输出 0.5。
        用于将余弦相似度平滑映射到概率区间。
        """
        if value >= 0:
            exp_value = math.exp(-value)
            return 1.0 / (1.0 + exp_value)
        # value < 0: 用等价公式 exp(x)/(1+exp(x)) 避免数值溢出
        exp_value = math.exp(value)
        return exp_value / (1.0 + exp_value)

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        """将值钳制在 [minimum, maximum] 范围内"""
        return max(minimum, min(maximum, value))
