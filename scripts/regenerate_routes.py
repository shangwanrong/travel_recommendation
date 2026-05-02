"""
重新生成全部路线（基于新爬取的POI数据）
删除旧路线，用 data_generator 基于真实POI数据重新生成
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from models.database import SessionLocal
from models.route import Route
from models.attraction import Attraction
from services.data_generator import RouteGenerator

CITIES = ['杭州', '成都', '西安', '厦门', '北京', '丽江', '上海',
          '三亚', '桂林', '青岛', '苏州', '南京', '重庆', '广州', '深圳']


def main():
    session = SessionLocal()
    generator = RouteGenerator()
    
    # 1. 删除所有旧路线
    old_count = session.query(Route).count()
    print(f"删除旧路线: {old_count} 条")
    session.query(Route).delete()
    session.commit()
    
    # 2. 检查每个城市的POI数量
    print(f"\n{'=' * 60}")
    print("各城市POI数量:")
    for city in CITIES:
        a_count = session.query(Attraction).filter_by(city=city).count()
        print(f"  {city}: {a_count} 个景点")
    
    # 3. 为每个城市生成路线
    print(f"\n{'=' * 60}")
    print("开始生成路线...")
    
    total = 0
    for city in CITIES:
        for days in [2, 3, 4, 5]:
            route_data = generator.generate_route(city, days)
            if route_data:
                # 确保route_id唯一
                existing = session.query(Route).filter_by(route_id=route_data['route_id']).first()
                if not existing:
                    if generator.save_route(route_data):
                        total += 1
                        print(f"  + {route_data['name']} ({route_data['route_id']})")
                else:
                    print(f"  skip (duplicate): {route_data['route_id']}")
            else:
                print(f"  x {city}{days}天 - 数据不足")
    
    generator.close()
    
    # 4. 验证匹配率
    print(f"\n{'=' * 60}")
    print("验证行程活动与POI坐标匹配率...")
    
    from models.hotel import Hotel
    from models.restaurant import Restaurant
    
    # 构建POI名称到坐标的映射
    poi_coords = {}
    for a in session.query(Attraction).all():
        if a.latitude and a.longitude:
            poi_coords[a.name] = [a.latitude, a.longitude]
    for h in session.query(Hotel).all():
        if h.latitude and h.longitude:
            poi_coords[h.name] = [h.latitude, h.longitude]
    for r in session.query(Restaurant).all():
        if r.latitude and r.longitude:
            poi_coords[r.name] = [r.latitude, r.longitude]
    
    routes = session.query(Route).all()
    total_acts = 0
    matched_acts = 0
    
    for route in routes:
        rd = route.to_dict()
        for day in rd.get('itinerary', []):
            for act in day.get('activities', []):
                total_acts += 1
                if act.get('name', '') in poi_coords:
                    matched_acts += 1
    
    match_rate = (matched_acts / total_acts * 100) if total_acts > 0 else 0
    
    print(f"  总活动数: {total_acts}")
    print(f"  匹配数: {matched_acts}")
    print(f"  匹配率: {match_rate:.1f}%")
    
    # 5. 最终统计
    print(f"\n{'=' * 60}")
    print(f"生成完成!")
    print(f"  新增路线: {total}")
    print(f"  总路线数: {session.query(Route).count()}")
    
    print(f"\n各城市路线:")
    for city in CITIES:
        count = session.query(Route).filter_by(city=city).count()
        print(f"  {city}: {count} 条")
    
    session.close()


if __name__ == '__main__':
    main()
