from flask import Blueprint, request, jsonify
from app.services.recommend.recommend_service import RecommendService

recommend_api = Blueprint('recommend_api', __name__)
recommend_service = RecommendService()

@recommend_api.route('/recipes', methods=['GET'])
def get_recommended_recipes():
    try:
        user_id = request.args.get('userId', type=int)
        goal_id = request.args.get('goalId', type=int)
        meal_type = request.args.get('mealType', '')
        limit = request.args.get('limit', 5, type=int)
        
        if not user_id:
            return jsonify({
                'code': 400,
                'message': 'userId is required'
            }), 400
        
        recipes = recommend_service.get_recommended_recipes(user_id, goal_id, meal_type, limit)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': recipes
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@recommend_api.route('/test', methods=['GET'])
def test_recommend():
    try:
        test_recipes = recommend_service.get_test_recipes()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': test_recipes
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500
