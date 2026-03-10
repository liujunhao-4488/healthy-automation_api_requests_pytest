import pandas as pd
import numpy as np

class HealthAnalyzer:
    def __init__(self):
        # 初始化健康分析引擎
        pass
    
    def analyze_health_data(self, user_id, health_data):
        # 分析健康数据
        analysis_result = {
            'bmi': {},
            'bmr': {},
            'nutrition_analysis': {},
            'recommendations': []
        }
        
        # 计算BMI
        if 'height' in health_data and 'weight' in health_data:
            height = health_data['height']  # 身高（cm）
            weight = health_data['weight']  # 体重（kg）
            bmi = self._calculate_bmi(height, weight)
            analysis_result['bmi'] = {
                'value': round(bmi, 2),
                'category': self._get_bmi_category(bmi),
                'status': self._get_bmi_status(bmi)
            }
        
        # 计算基础代谢率
        if 'age' in health_data and 'gender' in health_data and 'height' in health_data and 'weight' in health_data:
            age = health_data['age']
            gender = health_data['gender']
            height = health_data['height']
            weight = health_data['weight']
            bmr = self._calculate_bmr(age, gender, height, weight)
            analysis_result['bmr'] = {
                'value': round(bmr, 2),
                'description': '基础代谢率（卡路里/天）'
            }
        
        # 分析营养摄入
        if 'nutrition_data' in health_data:
            nutrition_data = health_data['nutrition_data']
            analysis_result['nutrition_analysis'] = self._analyze_nutrition(nutrition_data)
        
        # 生成健康建议
        analysis_result['recommendations'] = self._generate_recommendations(analysis_result)
        
        return analysis_result
    
    def _calculate_bmi(self, height, weight):
        # 计算BMI
        # BMI = 体重（kg）/ 身高（m）的平方
        height_m = height / 100
        return weight / (height_m ** 2)
    
    def _get_bmi_category(self, bmi):
        # 获取BMI分类
        if bmi < 18.5:
            return '偏瘦'
        elif 18.5 <= bmi < 24:
            return '正常'
        elif 24 <= bmi < 28:
            return '超重'
        else:
            return '肥胖'
    
    def _get_bmi_status(self, bmi):
        # 获取BMI状态描述
        if bmi < 18.5:
            return '体重过轻，建议适当增加营养摄入'
        elif 18.5 <= bmi < 24:
            return '体重正常，保持良好的生活习惯'
        elif 24 <= bmi < 28:
            return '体重超重，建议控制饮食并增加运动'
        else:
            return '体重肥胖，建议制定科学的减肥计划'
    
    def _calculate_bmr(self, age, gender, height, weight):
        # 计算基础代谢率
        # 使用Mifflin-St Jeor公式
        if gender == 'male':
            return 10 * weight + 6.25 * height - 5 * age + 5
        else:
            return 10 * weight + 6.25 * height - 5 * age - 161
    
    def _analyze_nutrition(self, nutrition_data):
        # 分析营养摄入
        analysis = {
            'total_calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'vitamins': 0,
            'minerals': 0,
            'imbalances': [],
            'recommendations': []
        }
        
        # 计算总营养摄入
        for item in nutrition_data:
            analysis['total_calories'] += item.get('calories', 0)
            analysis['protein'] += item.get('protein', 0)
            analysis['carbs'] += item.get('carbs', 0)
            analysis['fat'] += item.get('fat', 0)
            analysis['fiber'] += item.get('fiber', 0)
            analysis['vitamins'] += item.get('vitamins', 0)
            analysis['minerals'] += item.get('minerals', 0)
        
        # 分析营养平衡
        protein_ratio = (analysis['protein'] * 4) / analysis['total_calories'] if analysis['total_calories'] > 0 else 0
        carbs_ratio = (analysis['carbs'] * 4) / analysis['total_calories'] if analysis['total_calories'] > 0 else 0
        fat_ratio = (analysis['fat'] * 9) / analysis['total_calories'] if analysis['total_calories'] > 0 else 0
        
        # 检查营养比例是否合理
        if protein_ratio < 0.15:
            analysis['imbalances'].append('蛋白质摄入不足')
            analysis['recommendations'].append('建议增加蛋白质摄入，如瘦肉、鱼类、豆类等')
        elif protein_ratio > 0.35:
            analysis['imbalances'].append('蛋白质摄入过多')
            analysis['recommendations'].append('建议适当减少蛋白质摄入，保持营养平衡')
        
        if carbs_ratio < 0.45:
            analysis['imbalances'].append('碳水化合物摄入不足')
            analysis['recommendations'].append('建议增加碳水化合物摄入，如全谷物、蔬菜等')
        elif carbs_ratio > 0.65:
            analysis['imbalances'].append('碳水化合物摄入过多')
            analysis['recommendations'].append('建议适当减少碳水化合物摄入，选择低GI食物')
        
        if fat_ratio < 0.20:
            analysis['imbalances'].append('脂肪摄入不足')
            analysis['recommendations'].append('建议增加健康脂肪摄入，如橄榄油、坚果等')
        elif fat_ratio > 0.35:
            analysis['imbalances'].append('脂肪摄入过多')
            analysis['recommendations'].append('建议适当减少脂肪摄入，选择健康脂肪')
        
        # 检查膳食纤维摄入
        if analysis['fiber'] < 25:
            analysis['imbalances'].append('膳食纤维摄入不足')
            analysis['recommendations'].append('建议增加膳食纤维摄入，如蔬菜、水果、全谷物等')
        
        return analysis
    
    def _generate_recommendations(self, analysis_result):
        # 生成健康建议
        recommendations = []
        
        # 基于BMI的建议
        if 'bmi' in analysis_result:
            bmi_category = analysis_result['bmi']['category']
            if bmi_category == '偏瘦':
                recommendations.append('建议增加营养摄入，选择高热量密度的食物，如坚果、牛油果等')
                recommendations.append('适当进行力量训练，增加肌肉量')
            elif bmi_category == '超重':
                recommendations.append('建议控制总热量摄入，增加运动量')
                recommendations.append('选择低热量、高膳食纤维的食物')
            elif bmi_category == '肥胖':
                recommendations.append('建议制定科学的减肥计划，控制饮食并增加运动')
                recommendations.append('咨询专业营养师，获取个性化的饮食建议')
        
        # 基于营养分析的建议
        if 'nutrition_analysis' in analysis_result:
            nutrition_analysis = analysis_result['nutrition_analysis']
            if nutrition_analysis['recommendations']:
                recommendations.extend(nutrition_analysis['recommendations'])
        
        # 通用健康建议
        recommendations.append('保持充足的水分摄入，每天至少喝8杯水')
        recommendations.append('保证充足的睡眠时间，每天7-8小时')
        recommendations.append('定期进行身体活动，每周至少150分钟中等强度运动')
        
        return recommendations