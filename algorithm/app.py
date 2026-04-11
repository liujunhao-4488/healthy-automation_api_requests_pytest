from flask import Flask, request, jsonify
from flask_cors import CORS

from health_analyzer import HealthAnalyzer
from ingredient_substitute import IngredientSubstitute
from knowledge_recommender import KnowledgeRecommender
from recommend_engine import RecommendEngine

app = Flask(__name__)
CORS(app)

recommend_engine = RecommendEngine()
ingredient_substitute = IngredientSubstitute()
health_analyzer = HealthAnalyzer()
knowledge_recommender = KnowledgeRecommender()


@app.route('/api/recommend/recipes', methods=['POST'])
def recommend_recipes():
    try:
        data = request.json or {}
        recommended_recipes = recommend_engine.get_recommended_recipes(
            data.get('userId'),
            data.get('breakfastCount', 3),
            data.get('lunchCount', 3),
            data.get('dinnerCount', 3),
            data.get('healthInfo', {}),
            data.get('dietGoal', {}),
            data.get('candidateRecipes', [])
        )

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': recommended_recipes
        })
    except Exception as error:
        return jsonify({
            'code': 500,
            'message': str(error),
            'data': None
        })


@app.route('/api/recommend/substitute', methods=['POST'])
def substitute_ingredient():
    try:
        data = request.json or {}
        substitutes = ingredient_substitute.get_substitutes(
            data.get('ingredientName'),
            data.get('userId')
        )

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': substitutes
        })
    except Exception as error:
        return jsonify({
            'code': 500,
            'message': str(error),
            'data': None
        })


@app.route('/api/analyze/health', methods=['POST'])
def analyze_health():
    try:
        data = request.json or {}
        analysis_result = health_analyzer.analyze_health_data(
            data.get('userId'),
            data.get('healthData')
        )

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': analysis_result
        })
    except Exception as error:
        return jsonify({
            'code': 500,
            'message': str(error),
            'data': None
        })


@app.route('/api/recommend/articles', methods=['POST'])
def recommend_articles():
    try:
        data = request.json or {}
        recommended_articles = knowledge_recommender.get_recommended_articles(
            data.get('userId'),
            data.get('articleCount', 5)
        )

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': recommended_articles
        })
    except Exception as error:
        return jsonify({
            'code': 500,
            'message': str(error),
            'data': None
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
