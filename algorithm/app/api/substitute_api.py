from flask import Blueprint, request, jsonify
from app.services.substitute.substitute_service import SubstituteService

substitute_api = Blueprint('substitute_api', __name__)
substitute_service = SubstituteService()

@substitute_api.route('/ingredient', methods=['GET'])
def get_ingredient_substitutes():
    try:
        ingredient_id = request.args.get('ingredientId', type=int)
        limit = request.args.get('limit', 5, type=int)
        
        if not ingredient_id:
            return jsonify({
                'code': 400,
                'message': 'ingredientId is required'
            }), 400
        
        substitutes = substitute_service.get_ingredient_substitutes(ingredient_id, limit)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': substitutes
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@substitute_api.route('/test', methods=['GET'])
def test_substitute():
    try:
        test_substitutes = substitute_service.get_test_substitutes()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': test_substitutes
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500
