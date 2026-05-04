"""
MVP版本全面功能测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
from models.database import SessionLocal
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant
from models.route import Route
from app import app, get_city_name_map, get_poi_coords, load_cities

def test_database():
    """测试数据库完整性"""
    print("\n=== 1. 数据库完整性 ===")
    s = SessionLocal()
    
    stats = {
        'attractions': s.query(Attraction).count(),
        'hotels': s.query(Hotel).count(),
        'restaurants': s.query(Restaurant).count(),
        'routes': s.query(Route).count(),
        'cities': s.query(Route.city).distinct().count(),
    }
    
    print(f"  景点: {stats['attractions']}")
    print(f"  酒店: {stats['hotels']}")
    print(f"  餐厅: {stats['restaurants']}")
    print(f"  路线: {stats['routes']}")
    print(f"  城市: {stats['cities']}")
    
    # 检查坐标覆盖
    a_no_coords = sum(1 for a in s.query(Attraction).all() if not a.latitude)
    h_no_coords = sum(1 for h in s.query(Hotel).all() if not h.latitude)
    r_no_coords = sum(1 for r in s.query(Restaurant).all() if not r.latitude)
    
    print(f"  景点无坐标: {a_no_coords}")
    print(f"  酒店无坐标: {h_no_coords}")
    print(f"  餐厅无坐标: {r_no_coords}")
    
    if a_no_coords == 0 and h_no_coords == 0 and r_no_coords == 0:
        print("  [OK] 所有POI都有坐标")
    else:
        print("  [WARN] 有POI缺少坐标!")
    
    s.close()
    return stats


def test_poi_match_rate():
    """测试路线行程与POI坐标匹配率"""
    print("\n=== 2. 行程-坐标匹配率 ===")
    s = SessionLocal()
    
    poi_coords = get_poi_coords()
    print(f"  POI坐标总数: {len(poi_coords)}")
    
    routes = s.query(Route).all()
    total_acts = 0
    matched_acts = 0
    unmatched_names = set()
    
    for route in routes:
        rd = route.to_dict()
        for day in rd.get('itinerary', []):
            for act in day.get('activities', []):
                total_acts += 1
                name = act.get('name', '')
                if name in poi_coords:
                    matched_acts += 1
                else:
                    unmatched_names.add(name)
    
    rate = (matched_acts / total_acts * 100) if total_acts > 0 else 0
    print(f"  总活动: {total_acts}, 匹配: {matched_acts}, 未匹配: {total_acts - matched_acts}")
    print(f"  匹配率: {rate:.1f}%")
    
    if rate == 100:
        print("  [OK] 完美匹配!")
    elif rate >= 90:
        print("  [OK] 匹配率良好")
    else:
        print(f"  [WARN] 匹配率偏低! 未匹配样例:")
        for name in list(unmatched_names)[:10]:
            print(f"    - {name}")
    
    s.close()
    return rate


def test_api_endpoints():
    """测试API端点"""
    print("\n=== 3. API端点测试 ===")
    client = app.test_client()
    
    # 首页
    resp = client.get('/')
    print(f"  GET / : {resp.status_code}")
    
    # 城市列表
    resp = client.get('/api/cities')
    data = resp.get_json()
    print(f"  GET /api/cities : {resp.status_code}, {len(data)} 个省份")
    
    # 热门路线
    resp = client.get('/api/home')
    data = resp.get_json()
    print(f"  GET /api/home : {resp.status_code}, {len(data)} 条路线")
    if data and 'transport' in data[0]:
        print(f"    transport字段: {data[0]['transport']}")
    
    # 推荐路线
    name_map = get_city_name_map()
    test_cases = [
        ('hangzhou', 3, '杭州'),
        ('sanya', 2, '三亚'),
        ('shenzhen', 4, '深圳'),
        ('chongqing', 3, '重庆'),
    ]
    
    for city_id, days, city_name in test_cases:
        resp = client.post('/api/recommend', 
                          json={'city': city_id, 'days': days, 'transport': 'self-driving'},
                          content_type='application/json')
        data = resp.get_json()
        count = len(data) if isinstance(data, list) else 0
        print(f"  POST /api/recommend ({city_name}{days}天) : {resp.status_code}, {count} 条")
    
    # 统计
    resp = client.get('/api/stats')
    data = resp.get_json()
    print(f"  GET /api/stats : {resp.status_code}")
    print(f"    {data}")
    
    # 路线详情页
    s = SessionLocal()
    first_route = s.query(Route).first()
    s.close()
    
    if first_route:
        # 普通路线详情
        resp = client.get(f'/route/{first_route.route_id}')
        html = resp.data.decode('utf-8')
        print(f"  GET /route/{first_route.route_id} : {resp.status_code}")
        
        # 检查关键模板变量
        checks = {
            'amap_api_key': 'amap_api_key' in html,
            'poi_coords': 'poi_coords' in html,
            'routeData': 'routeData' in html,
            'initMap': 'initMap' in html,
            'focusOnMarker': 'focusOnMarker' in html,
            'cityCenters': 'cityCenters' in html,
            'skipLocation': 'skipLocation' in html,
        }
        for key, ok in checks.items():
            print(f"    {key}: {'OK' if ok else 'MISSING!'}")
        
        # 定制行程详情
        resp = client.get(f'/route/{first_route.route_id}?custom=1&transport=self-driving')
        html = resp.data.decode('utf-8')
        print(f"  GET /route/{first_route.route_id}?custom=1 : {resp.status_code}")
        
        custom_checks = {
            'isCustomRoute': 'isCustomRoute' in html,
            'locationModal': 'locationModal' in html,
            'skipLocation': 'skipLocation' in html,
        }
        for key, ok in custom_checks.items():
            print(f"    {key}: {'OK' if ok else 'MISSING!'}")


def test_consistency():
    """测试前后端一致性"""
    print("\n=== 4. 前后端一致性 ===")
    
    # 读取模板文件
    with open('templates/route_detail.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 检查关键一致性项
    issues = []
    
    # 1. amap_api_key (不是amap_key)
    if 'amap_key}}' in html and 'amap_api_key}}' not in html.split('amap_key}}')[0]:
        issues.append("模板仍使用amap_key而非amap_api_key")
    if 'amap_api_key' in html:
        print("  [OK] amap_api_key变量名一致")
    else:
        issues.append("模板缺少amap_api_key")
    
    # 2. cityCenters覆盖15个城市
    city_count = html.count("': [")  # 粗略统计cityCenters条目
    if city_count >= 15:
        print(f"  [OK] cityCenters覆盖{city_count}个城市")
    else:
        issues.append(f"cityCenters只有{city_count}个城市")
    
    # 3. accommodation和transport类型
    if "activity.type == 'accommodation'" in html:
        print("  [OK] 模板支持accommodation类型")
    else:
        issues.append("模板不支持accommodation类型")
    
    if "activity.type == 'transport'" in html:
        print("  [OK] 模板支持transport类型")
    else:
        issues.append("模板不支持transport类型")
    
    # 4. 跳过按钮
    if 'skipLocation' in html:
        print("  [OK] 位置弹窗有跳过按钮")
    else:
        issues.append("位置弹窗缺少跳过按钮")
    
    # 5. 地图立即初始化
    if 'if (!isCustomRoute)' not in html and 'initMap()' in html:
        print("  [OK] 地图对所有路线立即初始化")
    else:
        issues.append("定制行程可能不初始化地图")
    
    # 6. 读取app.py检查
    with open('app.py', 'r', encoding='utf-8') as f:
        app_code = f.read()
    
    if 'public-transport' in app_code:
        print("  [OK] 后端transport默认值使用public-transport")
    else:
        issues.append("后端transport默认值可能不一致")
    
    if 'get_city_name_map' in app_code:
        print("  [OK] 使用动态城市映射")
    else:
        issues.append("未使用动态城市映射")
    
    if issues:
        print(f"\n  [WARN] 发现{len(issues)}个问题:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("\n  [OK] 所有一致性检查通过!")


def main():
    print("=" * 60)
    print("MVP版本全面功能测试")
    print("=" * 60)
    
    stats = test_database()
    match_rate = test_poi_match_rate()
    test_api_endpoints()
    test_consistency()
    
    print(f"\n{'=' * 60}")
    print("测试总结:")
    print(f"  数据规模: {stats['attractions']}景点/{stats['hotels']}酒店/{stats['restaurants']}餐厅/{stats['routes']}路线/{stats['cities']}城市")
    print(f"  坐标匹配率: {match_rate:.1f}%")
    
    if match_rate >= 95 and stats['routes'] >= 60:
        print("  MVP状态: 可以展示!")
    else:
        print("  MVP状态: 需要修复")


if __name__ == '__main__':
    main()
