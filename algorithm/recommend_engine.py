import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class RecommendEngine:
    def __init__(self):
        # 初始化推荐引擎
        self.recipe_data = self._load_recipe_data()
        self.user_recipe_data = self._load_user_recipe_data()
        self.user_similarity_matrix = self._calculate_user_similarity()
    
    def _load_recipe_data(self):
        # 加载食谱数据（模拟数据）
        recipes = [
            {'id': 1, 'name': '燕麦粥', 'calories': 300, 'protein': 10, 'carbs': 50, 'fat': 5, 'meal_type': 'breakfast'},
            {'id': 2, 'name': '鸡蛋三明治', 'calories': 400, 'protein': 15, 'carbs': 45, 'fat': 15, 'meal_type': 'breakfast'},
            {'id': 3, 'name': '水果沙拉', 'calories': 200, 'protein': 5, 'carbs': 45, 'fat': 2, 'meal_type': 'breakfast'},
            {'id': 4, 'name': '鸡胸肉沙拉', 'calories': 450, 'protein': 30, 'carbs': 30, 'fat': 15, 'meal_type': 'lunch'},
            {'id': 5, 'name': '全麦意面', 'calories': 500, 'protein': 20, 'carbs': 60, 'fat': 10, 'meal_type': 'lunch'},
            {'id': 6, 'name': '蔬菜炒饭', 'calories': 400, 'protein': 15, 'carbs': 55, 'fat': 10, 'meal_type': 'lunch'},
            {'id': 7, 'name': '清蒸鱼', 'calories': 350, 'protein': 25, 'carbs': 10, 'fat': 15, 'meal_type': 'dinner'},
            {'id': 8, 'name': '烤鸡胸肉', 'calories': 300, 'protein': 25, 'carbs': 5, 'fat': 10, 'meal_type': 'dinner'},
            {'id': 9, 'name': '蔬菜汤', 'calories': 250, 'protein': 10, 'carbs': 30, 'fat': 5, 'meal_type': 'dinner'},
            {'id': 10, 'name': '酸奶碗', 'calories': 250, 'protein': 15, 'carbs': 30, 'fat': 8, 'meal_type': 'breakfast'},
            {'id': 11, 'name': '金枪鱼沙拉', 'calories': 400, 'protein': 25, 'carbs': 25, 'fat': 15, 'meal_type': 'lunch'},
            {'id': 12, 'name': '豆腐料理', 'calories': 300, 'protein': 20, 'carbs': 20, 'fat': 10, 'meal_type': 'dinner'}
        ]
        return pd.DataFrame(recipes)
    
    def _load_user_recipe_data(self):
        # 加载用户-食谱交互数据（模拟数据）
        interactions = [
            {'user_id': 1, 'recipe_id': 1, 'rating': 5},
            {'user_id': 1, 'recipe_id': 4, 'rating': 4},
            {'user_id': 1, 'recipe_id': 7, 'rating': 5},
            {'user_id': 2, 'recipe_id': 2, 'rating': 4},
            {'user_id': 2, 'recipe_id': 5, 'rating': 5},
            {'user_id': 2, 'recipe_id': 8, 'rating': 4},
            {'user_id': 3, 'recipe_id': 3, 'rating': 5},
            {'user_id': 3, 'recipe_id': 6, 'rating': 4},
            {'user_id': 3, 'recipe_id': 9, 'rating': 5},
            {'user_id': 4, 'recipe_id': 1, 'rating': 4},
            {'user_id': 4, 'recipe_id': 5, 'rating': 4},
            {'user_id': 4, 'recipe_id': 9, 'rating': 4},
            {'user_id': 5, 'recipe_id': 2, 'rating': 5},
            {'user_id': 5, 'recipe_id': 6, 'rating': 5},
            {'user_id': 5, 'recipe_id': 8, 'rating': 5}
        ]
        return pd.DataFrame(interactions)
    
    def _calculate_user_similarity(self):
        # 计算用户相似度矩阵
        # 创建用户-食谱评分矩阵
        user_recipe_matrix = self.user_recipe_data.pivot(index='user_id', columns='recipe_id', values='rating').fillna(0)
        
        # 计算用户之间的余弦相似度
        user_similarity = cosine_similarity(user_recipe_matrix)
        
        # 转换为DataFrame
        user_similarity_df = pd.DataFrame(user_similarity, index=user_recipe_matrix.index, columns=user_recipe_matrix.index)
        
        return user_similarity_df
    
    def get_recommended_recipes(self, user_id, breakfast_count=3, lunch_count=3, dinner_count=3):
        # 获取推荐食谱
        recommended_recipes = {
            'breakfast': [],
            'lunch': [],
            'dinner': []
        }
        
        # 获取每种餐型的推荐
        recommended_recipes['breakfast'] = self._recommend_by_meal_type(user_id, 'breakfast', breakfast_count)
        recommended_recipes['lunch'] = self._recommend_by_meal_type(user_id, 'lunch', lunch_count)
        recommended_recipes['dinner'] = self._recommend_by_meal_type(user_id, 'dinner', dinner_count)
        
        return recommended_recipes
    
    def _recommend_by_meal_type(self, user_id, meal_type, count):
        # 按餐型推荐食谱
        # 筛选对应餐型的食谱
        meal_recipes = self.recipe_data[self.recipe_data['meal_type'] == meal_type]
        
        # 获取用户已评分的食谱
        user_rated_recipes = self.user_recipe_data[self.user_recipe_data['user_id'] == user_id]['recipe_id'].tolist()
        
        # 计算食谱推荐分数
        recipe_scores = []
        for _, recipe in meal_recipes.iterrows():
            # 跳过用户已评分的食谱
            if recipe['id'] in user_rated_recipes:
                continue
            
            # 计算食谱推荐分数
            score = self._calculate_recipe_score(user_id, recipe['id'])
            recipe_scores.append((recipe, score))
        
        # 如果没有未评分的食谱，使用所有食谱
        if not recipe_scores:
            for _, recipe in meal_recipes.iterrows():
                score = self._calculate_recipe_score(user_id, recipe['id'])
                recipe_scores.append((recipe, score))
        
        # 按评分排序，取前count个
        recipe_scores.sort(key=lambda x: x[1], reverse=True)
        top_recipes = recipe_scores[:count]
        
        # 格式化推荐结果
        result = []
        for recipe, score in top_recipes:
            result.append({
                'id': recipe['id'],
                'name': recipe['name'],
                'calories': recipe['calories'],
                'protein': recipe['protein'],
                'carbs': recipe['carbs'],
                'fat': recipe['fat'],
                'score': round(score, 2)
            })
        
        return result
    
    def _calculate_recipe_score(self, user_id, recipe_id):
        # 计算食谱推荐分数
        # 检查用户是否在相似度矩阵中
        if user_id not in self.user_similarity_matrix.index:
            # 如果用户是新用户，返回默认分数
            return 3.0
        
        # 获取用户相似度
        user_similarities = self.user_similarity_matrix.loc[user_id]
        
        # 获取其他用户对该食谱的评分
        other_users_ratings = self.user_recipe_data[
            (self.user_recipe_data['recipe_id'] == recipe_id) & 
            (self.user_recipe_data['user_id'] != user_id)
        ]
        
        if other_users_ratings.empty:
            # 如果没有其他用户评分，返回默认分数
            return 3.0
        
        # 计算加权平均评分
        weighted_sum = 0
        similarity_sum = 0
        
        for _, row in other_users_ratings.iterrows():
            other_user_id = row['user_id']
            rating = row['rating']
            similarity = user_similarities.get(other_user_id, 0)
            
            weighted_sum += rating * similarity
            similarity_sum += similarity
        
        if similarity_sum == 0:
            return 3.0
        
        return weighted_sum / similarity_sum