import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class IngredientSubstitute:
    def __init__(self):
        # 初始化食材替代引擎
        self.ingredient_data = self._load_ingredient_data()
        self.nutrition_features = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'vitamins', 'minerals']
    
    def _load_ingredient_data(self):
        # 加载食材数据（模拟数据）
        ingredients = [
            {'id': 1, 'name': '鸡肉', 'category': 'meat', 'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0, 'vitamins': 5, 'minerals': 10},
            {'id': 2, 'name': '牛肉', 'category': 'meat', 'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 17, 'fiber': 0, 'vitamins': 4, 'minerals': 12},
            {'id': 3, 'name': '猪肉', 'category': 'meat', 'calories': 200, 'protein': 25, 'carbs': 0, 'fat': 10, 'fiber': 0, 'vitamins': 3, 'minerals': 9},
            {'id': 4, 'name': '鱼肉', 'category': 'meat', 'calories': 208, 'protein': 20, 'carbs': 0, 'fat': 13, 'fiber': 0, 'vitamins': 8, 'minerals': 15},
            {'id': 5, 'name': '豆腐', 'category': 'vegetable', 'calories': 76, 'protein': 8, 'carbs': 1.9, 'fat': 4.8, 'fiber': 0.3, 'vitamins': 2, 'minerals': 8},
            {'id': 6, 'name': '鸡蛋', 'category': 'dairy', 'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11, 'fiber': 0, 'vitamins': 12, 'minerals': 5},
            {'id': 7, 'name': '牛奶', 'category': 'dairy', 'calories': 42, 'protein': 3.4, 'carbs': 5, 'fat': 1, 'fiber': 0, 'vitamins': 10, 'minerals': 10},
            {'id': 8, 'name': '酸奶', 'category': 'dairy', 'calories': 59, 'protein': 10, 'carbs': 3.2, 'fat': 0.3, 'fiber': 0, 'vitamins': 8, 'minerals': 9},
            {'id': 9, 'name': '大米', 'category': 'grain', 'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4, 'vitamins': 1, 'minerals': 2},
            {'id': 10, 'name': '面条', 'category': 'grain', 'calories': 138, 'protein': 5.4, 'carbs': 28.9, 'fat': 0.7, 'fiber': 1.3, 'vitamins': 1, 'minerals': 3},
            {'id': 11, 'name': '燕麦', 'category': 'grain', 'calories': 389, 'protein': 16.9, 'carbs': 66, 'fat': 6.9, 'fiber': 10.6, 'vitamins': 6, 'minerals': 8},
            {'id': 12, 'name': '全麦面包', 'category': 'grain', 'calories': 69, 'protein': 3.6, 'carbs': 12, 'fat': 1, 'fiber': 1.9, 'vitamins': 3, 'minerals': 5},
            {'id': 13, 'name': '西红柿', 'category': 'vegetable', 'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2, 'fiber': 1.2, 'vitamins': 15, 'minerals': 6},
            {'id': 14, 'name': '胡萝卜', 'category': 'vegetable', 'calories': 41, 'protein': 0.9, 'carbs': 9.6, 'fat': 0.2, 'fiber': 2.8, 'vitamins': 20, 'minerals': 4},
            {'id': 15, 'name': '菠菜', 'category': 'vegetable', 'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'fiber': 2.2, 'vitamins': 25, 'minerals': 10},
            {'id': 16, 'name': '西兰花', 'category': 'vegetable', 'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'fiber': 2.6, 'vitamins': 20, 'minerals': 8},
            {'id': 17, 'name': '苹果', 'category': 'fruit', 'calories': 52, 'protein': 0.3, 'carbs': 13.8, 'fat': 0.2, 'fiber': 2.4, 'vitamins': 4, 'minerals': 3},
            {'id': 18, 'name': '香蕉', 'category': 'fruit', 'calories': 89, 'protein': 1.1, 'carbs': 22.8, 'fat': 0.3, 'fiber': 2.6, 'vitamins': 8, 'minerals': 4},
            {'id': 19, 'name': '橙子', 'category': 'fruit', 'calories': 47, 'protein': 0.9, 'carbs': 11.8, 'fat': 0.1, 'fiber': 2.4, 'vitamins': 30, 'minerals': 3},
            {'id': 20, 'name': '草莓', 'category': 'fruit', 'calories': 32, 'protein': 0.7, 'carbs': 7.7, 'fat': 0.3, 'fiber': 2, 'vitamins': 25, 'minerals': 2}
        ]
        return pd.DataFrame(ingredients)
    
    def get_substitutes(self, ingredient_name, user_id=None):
        # 获取食材替代建议
        # 查找目标食材
        target_ingredient = self.ingredient_data[self.ingredient_data['name'] == ingredient_name]
        
        if target_ingredient.empty:
            return []
        
        target_ingredient = target_ingredient.iloc[0]
        target_category = target_ingredient['category']
        
        # 提取目标食材的营养特征
        target_features = target_ingredient[self.nutrition_features].values.reshape(1, -1)
        
        # 计算与其他食材的相似度
        similarities = []
        for _, ingredient in self.ingredient_data.iterrows():
            # 排除自身
            if ingredient['name'] == ingredient_name:
                continue
            
            # 优先考虑同类别食材
            if ingredient['category'] == target_category:
                category_bonus = 0.3
            else:
                category_bonus = 0
            
            # 计算营养特征相似度
            ingredient_features = ingredient[self.nutrition_features].values.reshape(1, -1)
            similarity = cosine_similarity(target_features, ingredient_features)[0][0]
            
            # 综合相似度
            total_similarity = similarity + category_bonus
            similarities.append((ingredient, total_similarity))
        
        # 按相似度排序，取前5个
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_substitutes = similarities[:5]
        
        # 格式化结果
        result = []
        for ingredient, similarity in top_substitutes:
            result.append({
                'id': ingredient['id'],
                'name': ingredient['name'],
                'category': ingredient['category'],
                'similarity': round(similarity, 3),
                'nutrition': {
                    'calories': ingredient['calories'],
                    'protein': ingredient['protein'],
                    'carbs': ingredient['carbs'],
                    'fat': ingredient['fat'],
                    'fiber': ingredient['fiber'],
                    'vitamins': ingredient['vitamins'],
                    'minerals': ingredient['minerals']
                }
            })
        
        return result