from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from recommend_engine import RecommendEngine
from ingredient_substitute import IngredientSubstitute
from health_analyzer import HealthAnalyzer
from knowledge_recommender import KnowledgeRecommender

app = Flask(__name__)
CORS(app)

# 初始化算法模块
recommend_engine = RecommendEngine()
ingredient_substitute = IngredientSubstitute()
health_analyzer = HealthAnalyzer()
knowledge_recommender = KnowledgeRecommender()

@app.route('/api/recommend/recipes', methods=['POST'])
def recommend_recipes():
    try:
        data = request.json
        user_id = data.get('userId')
        breakfast_count = data.get('breakfastCount', 3)
        lunch_count = data.get('lunchCount', 3)
        dinner_count = data.get('dinnerCount', 3)
        
        # 获取推荐食谱
        recommended_recipes = recommend_engine.get_recommended_recipes(
            user_id, breakfast_count, lunch_count, dinner_count
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': recommended_recipes
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        })

@app.route('/api/recommend/substitute', methods=['POST'])
def substitute_ingredient():
    try:
        data = request.json
        ingredient_name = data.get('ingredientName')
        user_id = data.get('userId')
        
        # 获取食材替代建议
        substitutes = ingredient_substitute.get_substitutes(ingredient_name, user_id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': substitutes
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        })

@app.route('/api/analyze/health', methods=['POST'])
def analyze_health():
    try:
        data = request.json
        user_id = data.get('userId')
        health_data = data.get('healthData')
        
        # 分析健康数据
        analysis_result = health_analyzer.analyze_health_data(user_id, health_data)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': analysis_result
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        })

@app.route('/api/recommend/articles', methods=['POST'])
def recommend_articles():
    try:
        data = request.json
        user_id = data.get('userId')
        article_count = data.get('articleCount', 5)
        
        # 获取健康文章推荐
        recommended_articles = knowledge_recommender.get_recommended_articles(
            user_id, article_count
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': recommended_articles
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)