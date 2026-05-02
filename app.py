from flask import Flask, render_template, jsonify, request, send_file
import json
import os
from dotenv import load_dotenv
from functools import lru_cache
import logging
from export_itinerary import generate_itinerary_image
from models.database import SessionLocal
from models.route import Route
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON

# 获取高德地图API密钥
AMAP_API_KEY = os.getenv('AMAP_API_KEY', '')

# 全局POI坐标缓存
_poi_coords_cache = None

def get_db():
    """获取数据库会话"""
    return SessionLocal()

@lru_cache(maxsize=1)
def load_cities():
    """加载城市数据（带缓存）"""
    try:
        with open('data/cities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载城市数据失败: {e}")
        return {"provinces": []}

def get_poi_coords():
    """获取所有POI坐标（带缓存）"""
    global _poi_coords_cache

    if _poi_coords_cache is not None:
        return _poi_coords_cache

    db = get_db()
    try:
        poi_coords = {}

        # 获取景点坐标
        attractions = db.query(Attraction).all()
        for a in attractions:
            if a.latitude and a.longitude:
                poi_coords[a.name] = [a.latitude, a.longitude]

        # 获取酒店坐标
        hotels = db.query(Hotel).all()
        for h in hotels:
            if h.latitude and h.longitude:
                poi_coords[h.name] = [h.latitude, h.longitude]

        # 获取餐厅坐标
        restaurants = db.query(Restaurant).all()
        for r in restaurants:
            if r.latitude and r.longitude:
                poi_coords[r.name] = [r.latitude, r.longitude]

        _poi_coords_cache = poi_coords
        logger.info(f"POI坐标缓存已更新，共 {len(poi_coords)} 个")
        return poi_coords

    except Exception as e:
        logger.error(f"获取POI坐标失败: {e}")
        return {}
    finally:
        db.close()

def clear_poi_cache():
    """清除POI缓存"""
    global _poi_coords_cache
    _poi_coords_cache = None
    logger.info("POI坐标缓存已清除")

def get_city_name_map():
    """动态构建城市ID到中文名的映射（从cities.json加载，避免硬编码不同步）"""
    cities_data = load_cities()
    name_map = {}
    for prov in cities_data.get('provinces', []):
        for city in prov.get('cities', []):
            name_map[city['id']] = city['name']
    return name_map

# 错误处理
@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "资源未找到"}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器错误: {error}")
    if request.path.startswith('/api/'):
        return jsonify({"error": "服务器内部错误"}), 500
    return render_template('500.html'), 500

# 首页路由
@app.route('/')
def index():
    """首页"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"首页加载失败: {e}")
        return "页面加载失败", 500

# 路线详情页路由
@app.route('/route/<route_id>')
def route_detail(route_id):
    """路线详情页"""
    db = get_db()
    try:
        route = db.query(Route).filter_by(route_id=route_id).first()
        if not route:
            logger.warning(f"路线未找到: {route_id}")
            return "路线未找到", 404

        route_data = route.to_dict()

        # 使用缓存的POI坐标
        poi_coords = get_poi_coords()

        # 判断是否需要询问用户位置
        is_custom = request.args.get('custom', '0') == '1'

        # 获取出行方式
        transport = request.args.get('transport', 'self-driving')

        return render_template('route_detail.html',
                               route=route_data,
                               poi_coords=poi_coords,
                               is_custom=is_custom,
                               transport=transport,
                               amap_api_key=AMAP_API_KEY)
    except Exception as e:
        logger.error(f"路线详情页加载失败: {e}")
        return "页面加载失败", 500
    finally:
        db.close()

# API: 获取热门路线
@app.route('/api/home')
def api_home():
    """获取热门路线"""
    db = get_db()
    try:
        routes = db.query(Route).order_by(Route.popularity.desc()).limit(9).all()
        routes_data = [route.to_dict() for route in routes]
        # 统一为热门路线添加默认出行方式
        for route_data in routes_data:
            route_data['transport'] = 'self-driving'
        return jsonify(routes_data)
    except Exception as e:
        logger.error(f"获取热门路线失败: {e}")
        return jsonify({"error": "获取路线失败"}), 500
    finally:
        db.close()

# API: 获取城市列表
@app.route('/api/cities')
def api_cities():
    """获取城市列表"""
    try:
        cities = load_cities()
        province = request.args.get('province')

        if province:
            # 返回指定省份的城市
            for prov in cities['provinces']:
                if prov['name'] == province:
                    return jsonify(prov['cities'])
            return jsonify([])

        # 返回所有省份
        return jsonify(cities['provinces'])
    except Exception as e:
        logger.error(f"获取城市列表失败: {e}")
        return jsonify({"error": "获取城市列表失败"}), 500

# API: 智能推荐
@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """智能推荐路线"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        city = data.get('city')
        days = data.get('days')
        transport = data.get('transport', 'public-transport')  # 默认公共交通

        if not city:
            return jsonify({"error": "城市参数缺失"}), 400

        # 转换城市名称
        city_name = get_city_name_map().get(city, city)

        db = get_db()
        try:
            # 筛选匹配城市的路线
            query = db.query(Route).filter_by(city=city_name)

            # 优先选择天数匹配的路线（±1天）
            if days:
                try:
                    days = int(days)
                    exact_matches = query.filter(
                        Route.days >= days - 1,
                        Route.days <= days + 1
                    ).order_by(Route.popularity.desc()).limit(3).all()

                    if exact_matches:
                        routes_data = [route.to_dict() for route in exact_matches]
                        # 为每条路线添加出行方式标记
                        for route_data in routes_data:
                            route_data['transport'] = transport
                        return jsonify(routes_data)
                except ValueError:
                    logger.warning(f"无效的天数参数: {days}")

            # 如果没有精确匹配，返回该城市所有路线
            all_routes = query.order_by(Route.popularity.desc()).limit(3).all()
            routes_data = [route.to_dict() for route in all_routes]
            # 为每条路线添加出行方式标记
            for route_data in routes_data:
                route_data['transport'] = transport
            return jsonify(routes_data)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"智能推荐失败: {e}")
        return jsonify({"error": "推荐失败"}), 500

# API: 获取单个路线详情
@app.route('/api/route/<route_id>')
def api_route(route_id):
    """获取路线详情"""
    db = get_db()
    try:
        route = db.query(Route).filter_by(route_id=route_id).first()
        if route:
            return jsonify(route.to_dict())
        return jsonify({"error": "路线未找到"}), 404
    except Exception as e:
        logger.error(f"获取路线详情失败: {e}")
        return jsonify({"error": "获取路线失败"}), 500
    finally:
        db.close()

# API: 导出行程图片
@app.route('/api/export/<route_id>')
def export_route(route_id):
    """导出行程图片"""
    db = get_db()
    try:
        route = db.query(Route).filter_by(route_id=route_id).first()
        if not route:
            return jsonify({"error": "路线未找到"}), 404

        # 获取样式参数和出行方式
        style = request.args.get('style', 'modern_card')
        transport = request.args.get('transport', 'self-driving')

        # 转换为字典格式
        route_data = route.to_dict()

        # 添加出行方式信息
        route_data['transport'] = transport

        # 生成图片
        image_path = generate_itinerary_image(route_data, style=style)

        # 返回图片文件
        return send_file(
            image_path,
            as_attachment=True,
            download_name=f"{route_data['name']}_行程_{style}.png"
        )
    except Exception as e:
        logger.error(f"导出行程失败: {e}")
        return jsonify({"error": "导出失败"}), 500
    finally:
        db.close()

# API: 数据统计
@app.route('/api/stats')
def api_stats():
    """数据统计"""
    db = get_db()
    try:
        stats = {
            'routes': db.query(Route).count(),
            'attractions': db.query(Attraction).count(),
            'hotels': db.query(Hotel).count(),
            'restaurants': db.query(Restaurant).count(),
            'cities': db.query(Route.city).distinct().count()
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({"error": "获取统计失败"}), 500
    finally:
        db.close()

# API: 清除缓存（管理接口）
@app.route('/api/admin/clear-cache', methods=['POST'])
def clear_cache():
    """清除缓存"""
    try:
        clear_poi_cache()
        load_cities.cache_clear()
        return jsonify({"message": "缓存已清除"})
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return jsonify({"error": "清除缓存失败"}), 500

if __name__ == '__main__':
    logger.info("应用启动中...")
    app.run(debug=True, host='0.0.0.0', port=5000)
