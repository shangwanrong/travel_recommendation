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

# 定制路线内存缓存（路线数据太大无法存入session cookie，4KB限制）
_custom_routes_cache = {}

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


# ============ 智能定制功能 ============

@app.route('/customize')
def customize():
    """智能定制问卷页面"""
    return render_template('customize.html')


@app.route('/customize/results')
def customize_results():
    """定制路线结果展示页面"""
    session_id = request.args.get('session', '')
    routes = _custom_routes_cache.get(session_id)

    if not routes:
        # 如果缓存中没有数据，重定向到定制页面
        return render_template('customize.html')

    return render_template('customize_results.html',
                           routes=routes,
                           session_id=session_id,
                           amap_api_key=AMAP_API_KEY)


@app.route('/api/customize/generate', methods=['POST'])
def api_customize_generate():
    """根据用户偏好生成定制路线"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供偏好数据'}), 400

    # 提取参数
    preference = data.get('preference', 'balanced')
    pace = data.get('pace', 'moderate')
    city_id = data.get('city_id', '')
    city_name = data.get('city_name', '')
    days = data.get('days', 3)
    budget = data.get('budget', 3000)
    transport = data.get('transport', 'self-driving')

    if not city_id:
        return jsonify({'error': '请选择目的地城市'}), 400

    try:
        from services.route_generator import RouteGenerator
        generator = RouteGenerator()
        routes = generator.generate_routes(
            preference=preference,
            pace=pace,
            city_id=city_id,
            city_name=city_name,
            days=days,
            budget=budget,
            transport=transport
        )

        # 生成会话ID用于后续编辑
        import uuid
        session_id = str(uuid.uuid4())[:8]

        # 存入内存缓存（路线数据太大，无法存入session cookie的4KB限制）
        _custom_routes_cache[session_id] = routes

        return jsonify({
            'session_id': session_id,
            'routes': routes
        })

    except Exception as e:
        logger.error(f"生成定制路线失败: {e}")
        return jsonify({'error': f'生成路线失败: {str(e)}'}), 500


@app.route('/api/customize/optimize', methods=['POST'])
def api_customize_optimize():
    """优化路线顺序"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供路线数据'}), 400

    try:
        from services.route_optimizer import RouteOptimizer
        optimizer = RouteOptimizer()
        optimized = optimizer.optimize_route(data)

        return jsonify(optimized)

    except Exception as e:
        logger.error(f"优化路线失败: {e}")
        return jsonify({'error': f'优化路线失败: {str(e)}'}), 500


@app.route('/api/poi/suggestions')
def api_poi_suggestions():
    """获取POI建议列表"""
    city = request.args.get('city', '')
    category = request.args.get('category', '')
    poi_type = request.args.get('type', 'attraction')  # attraction/hotel/restaurant
    exclude_ids = request.args.get('exclude_ids', '')  # 逗号分隔的ID列表

    db = get_db()
    try:
        results = []
        exclude_list = [int(x) for x in exclude_ids.split(',') if x.strip()]

        if poi_type == 'attraction':
            query = db.query(Attraction).filter(Attraction.city == city)
            if category:
                query = query.filter(Attraction.category == category)
            if exclude_list:
                query = query.filter(~Attraction.id.in_(exclude_list))
            pois = query.order_by(Attraction.rating.desc()).limit(20).all()
            results = [{
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'suggested_duration': p.suggested_duration,
                'ticket_price': p.ticket_price,
                'latitude': p.latitude,
                'longitude': p.longitude,
                'rating': p.rating,
                'address': p.address,
                'tags': json.loads(p.tags) if p.tags else []
            } for p in pois]

        elif poi_type == 'hotel':
            query = db.query(Hotel).filter(Hotel.city == city)
            if exclude_list:
                query = query.filter(~Hotel.id.in_(exclude_list))
            pois = query.order_by(Hotel.rating.desc()).limit(20).all()
            results = [{
                'id': h.id,
                'name': h.name,
                'price_night': h.price_night,
                'price_range': h.price_range,
                'latitude': h.latitude,
                'longitude': h.longitude,
                'rating': h.rating,
                'address': h.address,
                'star_level': h.star_level
            } for h in pois]

        elif poi_type == 'restaurant':
            query = db.query(Restaurant).filter(Restaurant.city == city)
            if exclude_list:
                query = query.filter(~Restaurant.id.in_(exclude_list))
            pois = query.order_by(Restaurant.rating.desc()).limit(20).all()
            results = [{
                'id': r.id,
                'name': r.name,
                'avg_price': r.avg_price,
                'cuisine_type': r.cuisine_type,
                'latitude': r.latitude,
                'longitude': r.longitude,
                'rating': r.rating,
                'address': r.address,
                'tags': json.loads(r.tags) if r.tags else []
            } for r in pois]

        return jsonify({'pois': results, 'total': len(results)})

    except Exception as e:
        logger.error(f"获取POI建议失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/customize/save', methods=['POST'])
def api_customize_save():
    """保存定制路线到用户账户"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '请先登录'}), 401

    data = request.get_json()
    if not data or not data.get('route'):
        return jsonify({'error': '路线数据为空'}), 400

    route = data['route']
    db = get_db()
    try:
        from models.custom_route import CustomRoute
        import time

        # 生成唯一路线ID
        route_id = f"custom_{route.get('city_id', 'xx')}_{int(time.time())}"

        # 计算总时长
        total_duration = 0
        for day_plan in route.get('itinerary', []):
            total_duration += day_plan.get('total_time', 0)

        custom_route = CustomRoute(
            user_id=user_id,
            route_id=route_id,
            name=route.get('name', '定制路线'),
            city=route.get('city', ''),
            city_id=route.get('city_id', ''),
            days=route.get('days', 1),
            description=route.get('description', ''),
            total_budget=route.get('total_cost', 0),
            total_duration=round(total_duration / 60, 1),  # 转换为小时
            preference_data=json.dumps(data.get('preference', {})),
            itinerary=json.dumps(route.get('itinerary', [])),
            poi_data=json.dumps({}),
            transport_mode=route.get('transport_mode', 'self-driving'),
            is_finalized=1
        )

        db.add(custom_route)
        db.commit()

        return jsonify({'success': True, 'route_id': route_id, 'message': '路线已保存到个人中心'})

    except Exception as e:
        db.rollback()
        logger.error(f"保存定制路线失败: {e}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500
    finally:
        db.close()


@app.route('/api/user/custom_routes')
def api_user_custom_routes():
    """获取用户的定制路线列表"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '请先登录'}), 401

    db = get_db()
    try:
        from models.custom_route import CustomRoute
        routes = db.query(CustomRoute).filter(
            CustomRoute.user_id == user_id
        ).order_by(CustomRoute.created_at.desc()).all()

        return jsonify({
            'routes': [r.to_dict() for r in routes],
            'total': len(routes)
        })

    except Exception as e:
        logger.error(f"获取定制路线列表失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/customize/route/<route_id>')
def api_custom_route_detail(route_id):
    """获取定制路线详情"""
    db = get_db()
    try:
        from models.custom_route import CustomRoute
        route = db.query(CustomRoute).filter(CustomRoute.route_id == route_id).first()
        if not route:
            return jsonify({'error': '路线不存在'}), 404
        return jsonify(route.to_dict())
    except Exception as e:
        logger.error(f"获取定制路线详情失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/export/custom', methods=['POST'])
def export_custom_route():
    """导出定制路线为图片"""
    try:
        data = request.get_json()
        if not data or not data.get('route'):
            return jsonify({"error": "路线数据为空"}), 400

        custom_route = data['route']
        style = data.get('style', 'modern_card')

        # 将定制路线数据转换为导出样式所需的标准格式
        # 定制路线: itinerary[].attractions[], hotel, meals, transport
        # 标准格式: itinerary[].activities[], 每项含 time, type, name, description, price
        route_data = {
            'id': custom_route.get('city_id', 'custom'),
            'name': custom_route.get('name', '定制路线'),
            'city': custom_route.get('city', ''),
            'days': custom_route.get('days', 1),
            'description': custom_route.get('description', ''),
            'price_range': f"~{custom_route.get('total_cost', 0)}元",
            'transport': custom_route.get('transport_mode', 'public-transport'),
            'itinerary': []
        }

        for day_plan in custom_route.get('itinerary', []):
            day_data = {
                'day': day_plan.get('day', 1),
                'activities': []
            }

            # 景点
            for i, a in enumerate(day_plan.get('attractions', [])):
                duration = a.get('suggested_duration', 120)
                # 简易时间推算：从9:00开始
                start_hour = 9 + sum(
                    (prev_a.get('suggested_duration', 120) + 30) // 60
                    for prev_a in day_plan.get('attractions', [])[:i]
                )
                time_str = f"{start_hour:02d}:{(sum(prev_a.get('suggested_duration', 120) for prev_a in day_plan.get('attractions', [])[:i]) % 60):02d}"

                cat_name = {
                    'scenery': '自然风光', 'historical': '历史人文',
                    'entertainment': '休闲娱乐', 'religious': '宗教文化',
                    'shopping': '购物体验', 'leisure': '休闲放松'
                }.get(a.get('category', ''), '景点')

                day_data['activities'].append({
                    'time': time_str,
                    'type': 'attraction',
                    'name': a.get('name', ''),
                    'description': f"{cat_name} | 游玩{duration}分钟",
                    'latitude': a.get('latitude', 0),
                    'longitude': a.get('longitude', 0),
                    'price': a.get('ticket_price', 0)
                })

                # 交通段（在景点之间）
                transport = day_plan.get('transport', {})
                segments = transport.get('segments', [])
                if i < len(segments):
                    seg = segments[i]
                    mode_name = '自驾' if seg.get('mode') == 'driving' else '公共交通'
                    day_data['activities'].append({
                        'time': '',
                        'type': 'transport',
                        'name': f"{mode_name} {seg.get('distance', 0)}km",
                        'description': f"约{seg.get('time', 0)}分钟",
                        'price': 0
                    })

            # 午餐
            meals = day_plan.get('meals', {})
            if meals.get('lunch'):
                lunch = meals['lunch']
                day_data['activities'].append({
                    'time': '12:00',
                    'type': 'dining',
                    'name': f"午餐: {lunch.get('name', '')}",
                    'description': lunch.get('cuisine_type', ''),
                    'price': lunch.get('avg_price', 0)
                })

            # 晚餐
            if meals.get('dinner'):
                dinner = meals['dinner']
                day_data['activities'].append({
                    'time': '18:00',
                    'type': 'dining',
                    'name': f"晚餐: {dinner.get('name', '')}",
                    'description': dinner.get('cuisine_type', ''),
                    'price': dinner.get('avg_price', 0)
                })

            # 住宿
            hotel = day_plan.get('hotel')
            if hotel:
                day_data['activities'].append({
                    'time': '21:00',
                    'type': 'hotel',
                    'name': hotel.get('name', ''),
                    'description': f"¥{hotel.get('price_night', 0)}/晚",
                    'price': hotel.get('price_night', 0)
                })

            route_data['itinerary'].append(day_data)

        # 生成图片
        image_path = generate_itinerary_image(route_data, style=style)

        # 返回图片文件
        return send_file(
            image_path,
            as_attachment=True,
            download_name=f"{route_data['name']}_行程_{style}.png"
        )
    except Exception as e:
        logger.error(f"导出定制路线失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"导出失败: {str(e)}"}), 500


if __name__ == '__main__':
    logger.info("应用启动中...")
    app.run(debug=True, host='0.0.0.0', port=5000)
