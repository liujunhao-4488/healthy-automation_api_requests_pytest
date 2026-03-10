class Config:
    # 应用配置
    SECRET_KEY = 'health_diet_algorithm_secret_key'
    DEBUG = True
    
    # 数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'health_diet',
        'port': 3306
    }
    
    # 算法配置
    RECOMMEND_CONFIG = {
        'top_n': 10,
        'similarity_threshold': 0.6
    }
    
    # 食材替代配置
    SUBSTITUTE_CONFIG = {
        'top_n': 5,
        'nutrition_similarity_weight': 0.7,
        'category_similarity_weight': 0.3
    }
