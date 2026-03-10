import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class KnowledgeRecommender:
    def __init__(self):
        # 初始化知识推荐引擎
        self.article_data = self._load_article_data()
        self.user_preferences = self._load_user_preferences()
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        self.article_vectors = self._vectorize_articles()
    
    def _load_article_data(self):
        # 加载健康文章数据（模拟数据）
        articles = [
            {'id': 1, 'title': '健康饮食指南：如何平衡营养摄入', 'content': '健康饮食对于维持身体健康至关重要。本文将介绍如何平衡蛋白质、碳水化合物和脂肪的摄入，以及如何选择健康的食物。', 'category': 'nutrition', 'tags': ['nutrition', 'healthy_diet', 'balanced_diet']},
            {'id': 2, 'title': '减肥期间的饮食策略', 'content': '减肥是很多人的目标，但正确的饮食策略至关重要。本文将介绍如何在控制热量的同时保证营养摄入，以及如何避免常见的减肥误区。', 'category': 'weight_loss', 'tags': ['weight_loss', 'diet', 'calorie_control']},
            {'id': 3, 'title': '增肌必备：蛋白质摄入指南', 'content': '增肌需要足够的蛋白质摄入。本文将介绍不同人群的蛋白质需求，以及如何选择优质蛋白质来源。', 'category': 'muscle_gain', 'tags': ['muscle_gain', 'protein', 'fitness']},
            {'id': 4, 'title': '控糖饮食：如何管理血糖水平', 'content': '控糖对于糖尿病患者和预防糖尿病都非常重要。本文将介绍如何选择低GI食物，以及如何合理安排餐次。', 'category': 'blood_sugar', 'tags': ['blood_sugar', 'diabetes', 'low_gi']},
            {'id': 5, 'title': '心脏健康：如何通过饮食保护心脏', 'content': '心脏健康与饮食密切相关。本文将介绍如何通过饮食降低心脏病风险，以及哪些食物对心脏有益。', 'category': 'heart_health', 'tags': ['heart_health', 'cardiovascular', 'healthy_fats']},
            {'id': 6, 'title': '肠道健康：益生菌与膳食纤维的重要性', 'content': '肠道健康对于整体健康至关重要。本文将介绍益生菌和膳食纤维对肠道健康的益处，以及如何增加它们的摄入。', 'category': 'gut_health', 'tags': ['gut_health', 'probiotics', 'fiber']},
            {'id': 7, 'title': '运动营养：如何在运动前后合理饮食', 'content': '运动前后的饮食对于运动表现和恢复都非常重要。本文将介绍运动前后的营养需求，以及如何选择合适的食物。', 'category': 'sports_nutrition', 'tags': ['sports_nutrition', 'exercise', 'recovery']},
            {'id': 8, 'title': '儿童健康饮食：如何培养良好的饮食习惯', 'content': '儿童时期的饮食习惯会影响一生的健康。本文将介绍如何为儿童提供均衡的营养，以及如何培养良好的饮食习惯。', 'category': 'children_nutrition', 'tags': ['children', 'nutrition', 'healthy_habits']},
            {'id': 9, 'title': '老年人营养：如何应对年龄增长带来的营养挑战', 'content': '随着年龄的增长，营养需求会发生变化。本文将介绍老年人的特殊营养需求，以及如何通过饮食保持健康。', 'category': 'senior_nutrition', 'tags': ['senior', 'nutrition', 'healthy_aging']},
            {'id': 10, 'title': '素食者营养指南：如何在素食中获取足够的营养', 'content': '素食者需要特别注意某些营养素的摄入。本文将介绍素食者如何获取足够的蛋白质、铁、钙等营养素。', 'category': 'vegetarian', 'tags': ['vegetarian', 'nutrition', 'plant_based']}
        ]
        return pd.DataFrame(articles)
    
    def _load_user_preferences(self):
        # 加载用户偏好数据（模拟数据）
        user_preferences = [
            {'user_id': 1, 'preferred_categories': ['nutrition', 'weight_loss'], 'preferred_tags': ['healthy_diet', 'calorie_control']},
            {'user_id': 2, 'preferred_categories': ['muscle_gain', 'sports_nutrition'], 'preferred_tags': ['protein', 'fitness']},
            {'user_id': 3, 'preferred_categories': ['blood_sugar', 'heart_health'], 'preferred_tags': ['diabetes', 'cardiovascular']},
            {'user_id': 4, 'preferred_categories': ['gut_health', 'vegetarian'], 'preferred_tags': ['probiotics', 'plant_based']},
            {'user_id': 5, 'preferred_categories': ['children_nutrition', 'senior_nutrition'], 'preferred_tags': ['children', 'healthy_aging']}
        ]
        return pd.DataFrame(user_preferences)
    
    def _vectorize_articles(self):
        # 向量化文章内容
        # 合并标题和内容作为特征
        self.article_data['combined_text'] = self.article_data['title'] + ' ' + self.article_data['content']
        # 生成TF-IDF向量
        return self.tfidf_vectorizer.fit_transform(self.article_data['combined_text'])
    
    def get_recommended_articles(self, user_id, article_count=5):
        # 获取推荐文章
        # 查找用户偏好
        user_preference = self.user_preferences[self.user_preferences['user_id'] == user_id]
        
        if user_preference.empty:
            # 如果用户没有偏好记录，返回热门文章
            return self._get_popular_articles(article_count)
        
        user_preference = user_preference.iloc[0]
        preferred_categories = user_preference['preferred_categories']
        preferred_tags = user_preference['preferred_tags']
        
        # 计算文章与用户偏好的相似度
        article_scores = []
        for idx, article in self.article_data.iterrows():
            score = 0
            
            # 基于分类的评分
            if article['category'] in preferred_categories:
                score += 0.5
            
            # 基于标签的评分
            tag_match_count = len(set(article['tags']).intersection(set(preferred_tags)))
            score += tag_match_count * 0.2
            
            # 基于内容相似度的评分
            try:
                # 为用户偏好创建一个查询向量
                preference_text = ' '.join(preferred_categories + preferred_tags)
                preference_vector = self.tfidf_vectorizer.transform([preference_text])
                # 计算与当前文章的相似度
                content_similarity = cosine_similarity(preference_vector, self.article_vectors[idx])[0][0]
                score += content_similarity * 0.3
            except Exception as e:
                # 如果计算相似度失败，使用默认值
                score += 0.1
            
            article_scores.append((article, score))
        
        # 按评分排序，取前article_count个
        article_scores.sort(key=lambda x: x[1], reverse=True)
        top_articles = article_scores[:article_count]
        
        # 格式化结果
        result = []
        for article, score in top_articles:
            result.append({
                'id': article['id'],
                'title': article['title'],
                'category': article['category'],
                'tags': article['tags'],
                'relevance_score': round(score, 3)
            })
        
        return result
    
    def _get_popular_articles(self, article_count=5):
        # 获取热门文章（默认推荐）
        # 这里简单返回前article_count个文章
        popular_articles = []
        for _, article in self.article_data.head(article_count).iterrows():
            popular_articles.append({
                'id': article['id'],
                'title': article['title'],
                'category': article['category'],
                'tags': article['tags'],
                'relevance_score': 0.5  # 默认相关性评分
            })
        return popular_articles