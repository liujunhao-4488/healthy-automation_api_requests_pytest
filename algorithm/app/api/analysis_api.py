from flask import Blueprint, request, jsonify
from app.services.analysis.analysis_service import AnalysisService

analysis_api = Blueprint('analysis_api', __name__)
analysis_service = AnalysisService()

@analysis_api.route('/intake', methods=['POST'])
def analyze_intake():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        date_range = data.get('dateRange', {})
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        
        if not user_id:
            return jsonify({
                'code': 400,
                'message': 'userId is required'
            }), 400
        
        analysis_result = analysis_service.analyze_intake(user_id, start_date, end_date)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': analysis_result
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@analysis_api.route('/test', methods=['GET'])
def test_analysis():
    try:
        test_analysis = analysis_service.get_test_analysis()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': test_analysis
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500
