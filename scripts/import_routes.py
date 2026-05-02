"""
将routes.json中的路线数据导入到数据库
仅导入数据库中尚不存在的路线
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, init_db
from models.route import Route

def main():
    # 确保数据库表存在
    init_db()

    # 读取routes.json
    with open('data/routes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    session = SessionLocal()

    try:
        # 获取已存在的route_id
        existing_ids = set(r.route_id for r in session.query(Route.route_id).all())
        print(f"数据库已有 {len(existing_ids)} 条路线")

        new_count = 0
        skip_count = 0

        for route_data in data.get('routes', []):
            route_id = route_data.get('id', '')
            if route_id in existing_ids:
                skip_count += 1
                continue

            # 创建新路线
            route = Route(
                route_id=route_id,
                name=route_data.get('name', ''),
                city=route_data.get('city', ''),
                city_id=route_data.get('city_id', ''),
                province=route_data.get('province', ''),
                days=route_data.get('days', 0),
                description=route_data.get('description', ''),
                price_range=route_data.get('price_range', ''),
                cover_image=route_data.get('cover_image', ''),
                rating=4.5,
                popularity=route_data.get('popularity', 80),
                tags=json.dumps(route_data.get('tags', []), ensure_ascii=False),
                itinerary=json.dumps(route_data.get('itinerary', []), ensure_ascii=False)
            )
            session.add(route)
            new_count += 1
            print(f"  新增: {route_data.get('name', '')} ({route_data.get('city', '')})")

        session.commit()
        print(f"\n导入完成! 新增 {new_count} 条，跳过 {skip_count} 条已存在")

        # 统计
        total = session.query(Route).count()
        cities = set(r.city for r in session.query(Route.city).all())
        print(f"数据库总计: {total} 条路线，覆盖 {len(cities)} 个城市")
        print(f"城市列表: {', '.join(sorted(cities))}")

    except Exception as e:
        session.rollback()
        print(f"导入失败: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
