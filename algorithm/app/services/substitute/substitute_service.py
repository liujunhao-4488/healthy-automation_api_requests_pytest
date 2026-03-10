import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.config import Config

class SubstituteService:
    
    def __init__(self):
        self.config = Config()
        self.test_ingredients = self._load_test_ingredients()
    
    def get_ingredient_substitutes(self, ingredient_id, limit):
        """
        获取食材的替代方案
        基于营养成分相似度和类别相似度计算
        """
        # 查找目标食材
        target_ingredient = None
        for ing in self.test_ingredients:
            if ing['id'] == ingredient_id:
                target_ingredient = ing
                break
        
        if not target_ingredient:
            return []
        
        # 计算所有食材与目标食材的相似度
        substitutes = []
        for ing in self.test_ingredients:
            if ing['id'] != ingredient_id:
                similarity = self._calculate_similarity(target_ingredient, ing)
                if similarity > 0.3:  # 相似度阈值
                    substitutes.append({
                        'ingredientId': ing['id'],
                        'ingredientName': ing['name'],
                        'similarity': round(similarity, 2),
                        'nutritionInfo': {
                            'calories': ing['calories'],
                            'protein': ing['protein'],
                            'carbs': ing['carbs'],
                            'fat': ing['fat']
                        },
                        'substituteReason': self._generate_substitute_reason(target_ingredient, ing, similarity)
                    })
        
        # 按相似度排序
        substitutes.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 限制返回数量
        return substitutes[:limit]
    
    def get_test_substitutes(self):
        """
        获取测试食材替代数据
        """
        # 返回测试数据
        return [
            {
                'ingredientId': 2,
                'ingredientName': '面条',
                'similarity': 0.85,
                'nutritionInfo': {
                    'calories': 137,
                    'protein': 3.6,
                    'carbs': 28.9,
                    'fat': 0.7
                },
                'substituteReason': '面条和米饭都是主食，营养成分相似，可互相替代'
            },
            {
                'ingredientId': 5,
                'ingredientName': '鸡肉',
                'similarity': 0.78,
                'nutritionInfo': {
                    'calories': 165,
                    'protein': 31,
                    'carbs': 0,
                    'fat': 3.6
                },
                'substituteReason': '鸡肉和鱼肉都是高蛋白低脂肪的肉类，营养成分相似'
            }
        ]
    
    def _calculate_similarity(self, target_ing, candidate_ing):
        """
        计算两个食材的相似度
        """
        # 营养成分相似度
        nutrition_sim = self._calculate_nutrition_similarity(target_ing, candidate_ing)
        
        # 类别相似度
        category_sim = self._calculate_category_similarity(target_ing, candidate_ing)
        
        # 加权平均
        weight_nutrition = self.config.SUBSTITUTE_CONFIG['nutrition_similarity_weight']
        weight_category = self.config.SUBSTITUTE_CONFIG['category_similarity_weight']
        
        return nutrition_sim * weight_nutrition + category_sim * weight_category
    
    def _calculate_nutrition_similarity(self, ing1, ing2):
        """
        计算营养成分相似度
        """
        # 提取营养成分向量
        vec1 = np.array([
            ing1['calories'],
            ing1['protein'],
            ing1['carbs'],
            ing1['fat']
        ])
        
        vec2 = np.array([
            ing2['calories'],
            ing2['protein'],
            ing2['carbs'],
            ing2['fat']
        ])
        
        # 计算余弦相似度
        return cosine_similarity(vec1.reshape(1, -1), vec2.reshape(1, -1))[0][0]
    
    def _calculate_category_similarity(self, ing1, ing2):
        """
        计算类别相似度
        """
        # 相同类别相似度为1，不同为0
        return 1.0 if ing1['category'] == ing2['category'] else 0.0
    
    def _generate_substitute_reason(self, target_ing, candidate_ing, similarity):
        """
        生成替代原因
        """
        if similarity > 0.8:
            return f'{candidate_ing["name"]}和{target_ing["name"]}营养成分高度相似，是理想的替代品'
        elif similarity > 0.6:
            return f'{candidate_ing["name"]}和{target_ing["name"]}营养成分较为相似，可以作为替代品'
        else:
            return f'{candidate_ing["name"]}可以作为{target_ing["name"]}的替代选择'
    
    def _load_test_ingredients(self):
        """
        加载测试食材数据
        """
        return [
            {'id': 1, 'name': '米饭', 'category': '主食', 'calories': 116, 'protein': 2.6, 'carbs': 25.6, 'fat': 0.3},
            {'id': 2, 'name': '面条', 'category': '主食', 'calories': 137, 'protein': 3.6, 'carbs': 28.9, 'fat': 0.7},
            {'id': 3, 'name': '鸡蛋', 'category': '蛋类', 'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 10.6},
            {'id': 4, 'name': '牛奶', 'category': '乳制品', 'calories': 42, 'protein': 3.4, 'carbs': 5, 'fat': 1},
            {'id': 5, 'name': '鸡肉', 'category': '肉类', 'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6},
            {'id': 6, 'name': '牛肉', 'category': '肉类', 'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 17},
            {'id': 7, 'name': '猪肉', 'category': '肉类', 'calories': 337, 'protein': 13.2, 'carbs': 2.4, 'fat': 30.8},
            {'id': 8, 'name': '鱼肉', 'category': '肉类', 'calories': 124, 'protein': 20.4, 'carbs': 0, 'fat': 4.1},
            {'id': 9, 'name': '西红柿', 'category': '蔬菜', 'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2},
            {'id': 10, 'name': '黄瓜', 'category': '蔬菜', 'calories': 15, 'protein': 0.8, 'carbs': 3.6, 'fat': 0.1},
            {'id': 11, 'name': '白菜', 'category': '蔬菜', 'calories': 17, 'protein': 1.5, 'carbs': 3.2, 'fat': 0.1},
            {'id': 12, 'name': '胡萝卜', 'category': '蔬菜', 'calories': 41, 'protein': 0.9, 'carbs': 9.6, 'fat': 0.2},
            {'id': 13, 'name': '苹果', 'category': '水果', 'calories': 52, 'protein': 0.3, 'carbs': 13.8, 'fat': 0.2},
            {'id': 14, 'name': '香蕉', 'category': '水果', 'calories': 89, 'protein': 1.1, 'carbs': 22.8, 'fat': 0.3},
            {'id': 15, 'name': '橙子', 'category': '水果', 'calories': 47, 'protein': 0.9, 'carbs': 11.8, 'fat': 0.1}
        ]
