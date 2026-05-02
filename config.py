import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/travel.db')

    # 高德地图API配置
    AMAP_API_KEY = os.getenv('AMAP_API_KEY')
    AMAP_BASE_URL = 'https://restapi.amap.com/v3'

    # 数据采集配置
    REQUEST_TIMEOUT = 10
    REQUEST_DELAY = 0.5  # 请求间隔（秒）
    MAX_RETRIES = 3

    # 城市列表
    TARGET_CITIES = [
        '北京', '上海', '杭州', '成都', '西安',
        '厦门', '丽江', '三亚', '桂林', '青岛',
        '苏州', '南京', '重庆', '广州', '深圳'
    ]

    # POI类型配置
    POI_TYPES = {
        'attraction': '110000|110100|110200',  # 风景名胜
        'hotel': '100000',  # 住宿服务
        'restaurant': '050000'  # 餐饮服务
    }
