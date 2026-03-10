import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.config import Config

class RecommendService:
    
    def __init__(self):
        self.config = Config()
        self.test_recipes = self._load_test_recipes()
    
    def get_recommended_recipes(self, user_id, goal_id, meal_type, limit):
        """
        获取推荐食谱
        使用协同过滤算法结合用户健康信息和饮食目标
        """
        # 这里实现协同过滤推荐算法
        # 由于是演示，暂时返回测试数据
        filtered_recipes = self.test_recipes
        
        # 根据餐型过滤
        if meal_type:
            filtered_recipes = [r for r in filtered_recipes if r['meal_type'] == meal_type]
        
        # 限制返回数量
        return filtered_recipes[:limit]
    
    def get_test_recipes(self):
        """
        获取测试食谱数据
        """
        return self.test_recipes
    
    def _load_test_recipes(self):
        """
        加载测试食谱数据
        """
        return [
            {
                'recipeId': 1,
                'recipeName': '清蒸鱼',
                'calories': 200,
                'protein': 25,
                'carbs': 5,
                'fat': 8,
                'cookingTime': 20,
                'difficulty': '简单',
                'meal_type': 'dinner',
                'ingredients': [
                    {'id': 8, 'name': '鱼肉', 'quantity': '300g'},
                    {'id': 9, 'name': '西红柿', 'quantity': '1个'},
                    {'id': 10, 'name': '黄瓜', 'quantity': '半根'}
                ]
            },
            {
                'recipeId': 2,
                'recipeName': '鸡胸肉沙拉',
                'calories': 350,
                'protein': 35,
                'carbs': 15,
                'fat': 12,
                'cookingTime': 15,
                'difficulty': '简单',
                'meal_type': 'lunch',
                'ingredients': [
                    {'id': 5, 'name': '鸡肉', 'quantity': '200g'},
                    {'id': 9, 'name': '西红柿', 'quantity': '1个'},
                    {'id': 10, 'name': '黄瓜', 'quantity': '1根'},
                    {'id': 11, 'name': '白菜', 'quantity': '100g'}
                ]
            },
            {
                'recipeId': 3,
                'recipeName': '全麦三明治',
                'calories': 300,
                'protein': 20,
                'carbs': 35,
                'fat': 10,
                'cookingTime': 10,
                'difficulty': '简单',
                'meal_type': 'breakfast',
                'ingredients': [
                    {'id': 2, 'name': '面条', 'quantity': '50g'},
                    {'id': 3, 'name': '鸡蛋', 'quantity': '1个'},
                    {'id': 4, 'name': '牛奶', 'quantity': '100ml'}
                ]
            },
            {
                'recipeId': 4,
                'recipeName': '蔬菜炒饭',
                'calories': 400,
                'protein': 15,
                'carbs': 50,
                'fat': 15,
                'cookingTime': 15,
                'difficulty': '中等',
                'meal_type': 'lunch',
                'ingredients': [
                    {'id': 1, 'name': '米饭', 'quantity': '150g'},
                    {'id': 9, 'name': '西红柿', 'quantity': '1个'},
                    {'id': 10, 'name': '黄瓜', 'quantity': '半根'},
                    {'id': 12, 'name': '胡萝卜', 'quantity': '半根'}
                ]
            },
            {
                'recipeId': 5,
                'recipeName': '牛肉蔬菜汤',
                'calories': 250,
                'protein': 20,
                'carbs': 10,
                'fat': 15,
                'cookingTime': 30,
                'difficulty': '中等',
                'meal_type': 'dinner',
                'ingredients': [
                    {'id': 6, 'name': '牛肉', 'quantity': '200g'},
                    {'id': 11, 'name': '白菜', 'quantity': '200g'},
                    {'id': 12, 'name': '胡萝卜', 'quantity': '1根'}
                ]
            },
            {
                'recipeId': 6,
                'recipeName': '香蕉牛奶燕麦',
                'calories': 320,
                'protein': 12,
                'carbs': 45,
                'fat': 10,
                'cookingTime': 5,
                'difficulty': '简单',
                'meal_type': 'breakfast',
                'ingredients': [
                    {'id': 4, 'name': '牛奶', 'quantity': '200ml'},
                    {'id': 13, 'name': '苹果', 'quantity': '1个'},
                    {'id': 14, 'name': '香蕉', 'quantity': '1根'}
                ]
            }
        ]
    
    def _calculate_similarity(self, user_features, recipe_features):
        """
        计算用户与食谱的相似度
        """
        user_vec = np.array(user_features).reshape(1, -1)
        recipe_vec = np.array(recipe_features).reshape(1, -1)
        return cosine_similarity(user_vec, recipe_vec)[0][0]
