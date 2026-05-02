from flask import Flask, render_template, jsonify, request, send_file, session
import json
import os
from dotenv import load_dotenv
from functools import lru_cache
import logging
from datetime import datetime
from export_itinerary import generate_itinerary_image
from models.database import SessionLocal
from models.route import Route
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant
from models.user import User
from models.user_data import Favorite, Footprint, BrowseHistory

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
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

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
        transport = data.get('transport', 'public-transport')  # 默认公共交通

        if not city:
            return jsonify({"error": "城市参数缺失"}), 400

        # 转换城市名称
        city_name = get_city_name_map().get(city, city)

        db = get_db()
        try:
            # 筛选匹配城市的路线，按热度排序
            all_routes = db.query(Route).filter_by(city=city_name).order_by(Route.popularity.desc()).limit(4).all()
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

# ============ 用户认证辅助函数 ============

def get_current_user():
    """从session获取当前登录用户"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    try:
        return db.query(User).get(user_id)
    finally:
        db.close()

def login_required_api():
    """API登录检查装饰器返回值，如果未登录返回错误响应"""
    if not session.get('user_id'):
        return jsonify({"error": "请先登录", "need_login": True}), 401
    return None

# ============ 用户认证API ============

@app.route('/api/register', methods=['POST'])
def api_register():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()

        if not username or not password:
            return jsonify({"error": "用户名和密码不能为空"}), 400
        if len(username) < 2 or len(username) > 20:
            return jsonify({"error": "用户名长度应为2-20个字符"}), 400
        if len(password) < 6:
            return jsonify({"error": "密码长度至少6个字符"}), 400

        db = get_db()
        try:
            # 检查用户名是否已存在
            existing = db.query(User).filter_by(username=username).first()
            if existing:
                return jsonify({"error": "用户名已存在"}), 409

            # 检查邮箱是否已存在
            if email:
                existing_email = db.query(User).filter_by(email=email).first()
                if existing_email:
                    return jsonify({"error": "邮箱已被注册"}), 409

            # 创建用户
            user = User(username=username, email=email or None)
            user.set_password(password)
            db.add(user)
            db.commit()

            # 自动登录
            session['user_id'] = user.id
            session['username'] = user.username

            return jsonify({"message": "注册成功", "user": user.to_dict()}), 201
        finally:
            db.close()
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return jsonify({"error": "注册失败，请重试"}), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    """用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({"error": "用户名和密码不能为空"}), 400

        db = get_db()
        try:
            user = db.query(User).filter_by(username=username).first()
            if not user or not user.check_password(password):
                return jsonify({"error": "用户名或密码错误"}), 401

            # 设置session
            session['user_id'] = user.id
            session['username'] = user.username

            return jsonify({"message": "登录成功", "user": user.to_dict()})
        finally:
            db.close()
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({"error": "登录失败，请重试"}), 500


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """用户登出"""
    session.clear()
    return jsonify({"message": "已退出登录"})


@app.route('/api/user/info')
def api_user_info():
    """获取当前登录用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"user": None})

    db = get_db()
    try:
        user = db.query(User).get(user_id)
        if not user:
            session.clear()
            return jsonify({"user": None})

        # 获取统计信息
        fav_count = db.query(Favorite).filter_by(user_id=user_id).count()
        footprint_count = db.query(Footprint).filter_by(user_id=user_id).count()
        history_count = db.query(BrowseHistory).filter_by(user_id=user_id).count()

        user_data = user.to_dict()
        user_data['fav_count'] = fav_count
        user_data['footprint_count'] = footprint_count
        user_data['history_count'] = history_count

        return jsonify({"user": user_data})
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return jsonify({"user": None})
    finally:
        db.close()


# ============ 收藏API ============

@app.route('/api/favorite', methods=['POST'])
def api_add_favorite():
    """收藏路线"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        data = request.get_json()
        route_id = data.get('route_id')
        if not route_id:
            return jsonify({"error": "路线ID缺失"}), 400

        user_id = session['user_id']
        db = get_db()
        try:
            # 检查是否已收藏
            existing = db.query(Favorite).filter_by(user_id=user_id, route_id=route_id).first()
            if existing:
                return jsonify({"error": "已收藏过该路线"}), 409

            # 检查路线是否存在
            route = db.query(Route).filter_by(route_id=route_id).first()
            if not route:
                return jsonify({"error": "路线不存在"}), 404

            favorite = Favorite(user_id=user_id, route_id=route_id)
            db.add(favorite)
            db.commit()

            return jsonify({"message": "收藏成功"}), 201
        finally:
            db.close()
    except Exception as e:
        logger.error(f"收藏失败: {e}")
        return jsonify({"error": "收藏失败"}), 500


@app.route('/api/favorite/<route_id>', methods=['DELETE'])
def api_remove_favorite(route_id):
    """取消收藏"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        user_id = session['user_id']
        db = get_db()
        try:
            favorite = db.query(Favorite).filter_by(user_id=user_id, route_id=route_id).first()
            if not favorite:
                return jsonify({"error": "未收藏该路线"}), 404

            db.delete(favorite)
            db.commit()

            return jsonify({"message": "已取消收藏"})
        finally:
            db.close()
    except Exception as e:
        logger.error(f"取消收藏失败: {e}")
        return jsonify({"error": "操作失败"}), 500


@app.route('/api/favorites')
def api_get_favorites():
    """获取用户收藏列表"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        user_id = session['user_id']
        db = get_db()
        try:
            favorites = db.query(Favorite).filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()
            route_ids = [f.route_id for f in favorites]

            routes = []
            for rid in route_ids:
                route = db.query(Route).filter_by(route_id=rid).first()
                if route:
                    route_data = route.to_dict()
                    route_data['favorited_at'] = next(
                        (f.created_at.strftime('%Y-%m-%d %H:%M') for f in favorites if f.route_id == rid), ''
                    )
                    routes.append(route_data)

            return jsonify({"favorites": routes, "total": len(routes)})
        finally:
            db.close()
    except Exception as e:
        logger.error(f"获取收藏列表失败: {e}")
        return jsonify({"error": "获取失败"}), 500


@app.route('/api/favorite/check/<route_id>')
def api_check_favorite(route_id):
    """检查路线是否已收藏"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"is_favorited": False})

    db = get_db()
    try:
        existing = db.query(Favorite).filter_by(user_id=user_id, route_id=route_id).first()
        return jsonify({"is_favorited": existing is not None})
    finally:
        db.close()


# ============ 足迹API ============

@app.route('/api/footprint', methods=['POST'])
def api_add_footprint():
    """添加旅行足迹（按景点标记）"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        data = request.get_json()
        city = data.get('city')
        city_id = data.get('city_id', '')
        attraction_name = data.get('attraction_name', '')
        latitude = data.get('latitude', '')
        longitude = data.get('longitude', '')

        if not city:
            return jsonify({"error": "城市名称缺失"}), 400
        if not attraction_name:
            return jsonify({"error": "景点名称缺失"}), 400

        user_id = session['user_id']
        db = get_db()
        try:
            existing = db.query(Footprint).filter_by(user_id=user_id, attraction_name=attraction_name).first()
            if existing:
                return jsonify({"message": "该景点已在足迹中"})

            footprint = Footprint(
                user_id=user_id, city=city, city_id=city_id,
                attraction_name=attraction_name,
                latitude=str(latitude) if latitude else '',
                longitude=str(longitude) if longitude else ''
            )
            db.add(footprint)
            db.commit()

            return jsonify({"message": "足迹添加成功"}), 201
        finally:
            db.close()
    except Exception as e:
        logger.error(f"添加足迹失败: {e}")
        return jsonify({"error": "操作失败"}), 500


@app.route('/api/footprints')
def api_get_footprints():
    """获取用户足迹"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        user_id = session['user_id']
        db = get_db()
        try:
            footprints = db.query(Footprint).filter_by(user_id=user_id).order_by(Footprint.visited_at.desc()).all()
            return jsonify({
                "footprints": [f.to_dict() for f in footprints],
                "total": len(footprints)
            })
        finally:
            db.close()
    except Exception as e:
        logger.error(f"获取足迹失败: {e}")
        return jsonify({"error": "获取失败"}), 500


# ============ 浏览历史API ============

@app.route('/api/history', methods=['POST'])
def api_add_history():
    """记录浏览历史"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        data = request.get_json()
        route_id = data.get('route_id')
        if not route_id:
            return jsonify({"error": "路线ID缺失"}), 400

        user_id = session['user_id']
        db = get_db()
        try:
            # 删除同一路线的旧记录，只保留最新一次
            db.query(BrowseHistory).filter_by(user_id=user_id, route_id=route_id).delete()

            history = BrowseHistory(user_id=user_id, route_id=route_id)
            db.add(history)
            db.commit()

            return jsonify({"message": "记录成功"}), 201
        finally:
            db.close()
    except Exception as e:
        logger.error(f"记录浏览历史失败: {e}")
        return jsonify({"error": "记录失败"}), 500


@app.route('/api/history')
def api_get_history():
    """获取浏览历史"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        user_id = session['user_id']
        db = get_db()
        try:
            histories = db.query(BrowseHistory).filter_by(user_id=user_id).order_by(BrowseHistory.viewed_at.desc()).limit(20).all()
            route_ids = [h.route_id for h in histories]

            routes = []
            for rid in route_ids:
                route = db.query(Route).filter_by(route_id=rid).first()
                if route:
                    route_data = route.to_dict()
                    route_data['viewed_at'] = next(
                        (h.viewed_at.strftime('%Y-%m-%d %H:%M') for h in histories if h.route_id == rid), ''
                    )
                    routes.append(route_data)

            return jsonify({"history": routes, "total": len(routes)})
        finally:
            db.close()
    except Exception as e:
        logger.error(f"获取浏览历史失败: {e}")
        return jsonify({"error": "获取失败"}), 500


@app.route('/api/history', methods=['DELETE'])
def api_clear_history():
    """清空浏览历史"""
    auth_check = login_required_api()
    if auth_check:
        return auth_check

    try:
        user_id = session['user_id']
        db = get_db()
        try:
            db.query(BrowseHistory).filter_by(user_id=user_id).delete()
            db.commit()
            return jsonify({"message": "历史已清空"})
        finally:
            db.close()
    except Exception as e:
        logger.error(f"清空历史失败: {e}")
        return jsonify({"error": "操作失败"}), 500


# ============ 个人中心页面 ============

@app.route('/profile')
def profile():
    """个人中心页面"""
    user_id = session.get('user_id')
    if not user_id:
        return render_template('index.html')

    return render_template('profile.html')


if __name__ == '__main__':
    logger.info("应用启动中...")
    app.run(debug=True, host='0.0.0.0', port=5000)
