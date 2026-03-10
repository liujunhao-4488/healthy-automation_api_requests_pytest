import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class AnalysisService:
    
    def __init__(self):
        pass
    
    def analyze_intake(self, user_id, start_date, end_date):
        """
        分析用户的饮食摄入情况
        生成热量和营养摄入趋势
        """
        # 这里实现饮食摄入分析算法
        # 由于是演示，暂时返回测试数据
        return self._generate_test_analysis()
    
    def get_test_analysis(self):
        """
        获取测试分析数据
        """
        return self._generate_test_analysis()
    
    def _generate_test_analysis(self):
        """
        生成测试分析数据
        """
        # 生成最近7天的日期
        dates = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
            dates.append(date)
        
        # 生成测试数据
        return {
            'summary': {
                'totalCalories': 18500,
                'averageCalories': 2642.86,
                'totalProtein': 650,
                'averageProtein': 92.86,
                'totalCarbs': 2100,
                'averageCarbs': 300,
                'totalFat': 550,
                'averageFat': 78.57
            },
            'trends': {
                'calories': [
                    {'date': dates[0], 'value': 2500},
                    {'date': dates[1], 'value': 2700},
                    {'date': dates[2], 'value': 2600},
                    {'date': dates[3], 'value': 2800},
                    {'date': dates[4], 'value': 2500},
                    {'date': dates[5], 'value': 2700},
                    {'date': dates[6], 'value': 2700}
                ],
                'protein': [
                    {'date': dates[0], 'value': 85},
                    {'date': dates[1], 'value': 95},
                    {'date': dates[2], 'value': 90},
                    {'date': dates[3], 'value': 100},
                    {'date': dates[4], 'value': 85},
                    {'date': dates[5], 'value': 95},
                    {'date': dates[6], 'value': 95}
                ],
                'carbs': [
                    {'date': dates[0], 'value': 280},
                    {'date': dates[1], 'value': 320},
                    {'date': dates[2], 'value': 300},
                    {'date': dates[3], 'value': 330},
                    {'date': dates[4], 'value': 280},
                    {'date': dates[5], 'value': 310},
                    {'date': dates[6], 'value': 300}
                ],
                'fat': [
                    {'date': dates[0], 'value': 75},
                    {'date': dates[1], 'value': 80},
                    {'date': dates[2], 'value': 78},
                    {'date': dates[3], 'value': 85},
                    {'date': dates[4], 'value': 72},
                    {'date': dates[5], 'value': 80},
                    {'date': dates[6], 'value': 80}
                ]
            },
            'recommendations': [
                '蛋白质摄入充足，继续保持',
                '碳水化合物摄入略高，建议适当减少',
                '脂肪摄入在合理范围内',
                '建议增加蔬菜和水果的摄入量'
            ]
        }
