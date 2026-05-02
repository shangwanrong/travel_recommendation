"""
基于爬取的POI数据批量生成路线
为15个城市每个生成3-5条不同天数的路线
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.route import Route
from services.data_generator import RouteGenerator

CITIES = ['杭州', '成都', '西安', '厦门', '北京', '丽江', '上海',
          '三亚', '桂林', '青岛', '苏州', '南京', '重庆', '广州', '深圳']

def main():
    session = SessionLocal()
    generator = RouteGenerator()
    
    total_generated = 0
    total_skipped = 0
    
    print("=" * 60)
    print("批量生成路线（基于爬取的POI数据）")
    print("=" * 60)
    
    # 检查每个城市现有路线数
    for city in CITIES:
        existing = session.query(Route).filter_by(city=city).count()
        print(f"\n{city}: 现有 {existing} 条路线")
    
    print(f"\n{'=' * 60}")
    print("开始生成...")
    
    for city in CITIES:
        for days in [2, 3, 4, 5]:
            # 检查是否已有相同天数的路线
            existing = session.query(Route).filter_by(city=city, days=days).count()
            if existing >= 2:
                print(f"  {city}{days}天路线已有{existing}条，跳过")
                total_skipped += 1
                continue
            
            # 生成新路线
            route_data = generator.generate_route(city, days)
            if route_data:
                # 检查route_id是否已存在
                existing_route = session.query(Route).filter_by(route_id=route_data['route_id']).first()
                if not existing_route:
                    if generator.save_route(route_data):
                        total_generated += 1
                        print(f"  + {route_data['name']} ({route_data['route_id']})")
                else:
                    print(f"  跳过（已存在）: {route_data['route_id']}")
            else:
                print(f"  x {city}{days}天 - 数据不足")
    
    generator.close()
    
    # 统计
    print(f"\n{'=' * 60}")
    print(f"生成完成!")
    print(f"  新增路线: {total_generated}")
    print(f"  跳过: {total_skipped}")
    
    total_routes = session.query(Route).count()
    print(f"  总路线数: {total_routes}")
    
    print(f"\n各城市路线数:")
    for city in CITIES:
        count = session.query(Route).filter_by(city=city).count()
        bar = '#' * min(count, 20)
        print(f"  {city:4s}: {count:3d} {bar}")
    
    session.close()

if __name__ == '__main__':
    main()
