"""
修复厦门路线中的错误景点
删除包含北京景点的厦门路线，并重新生成
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.route import Route
from services.data_generator import RouteGenerator
import json

def fix_xiamen_routes():
    db = SessionLocal()

    try:
        # 删除有问题的厦门路线
        problem_routes = ['xiamen-2days-347', 'xiamen-4days-879']

        for route_id in problem_routes:
            route = db.query(Route).filter_by(route_id=route_id).first()
            if route:
                print(f"Deleting problematic route: {route.name} ({route_id})")
                db.delete(route)

        db.commit()
        print("\n[OK] Deleted 2 problematic routes")

        # 重新生成这2条路线
        print("\nRegenerating routes...")
        generator = RouteGenerator()

        # 生成2天路线
        route_data = generator.generate_route('厦门', 2, 'xiamen-2days-347')
        if route_data:
            generator.save_route(route_data)
            print(f"[OK] Generated: {route_data['name']}")

        # 生成4天路线
        route_data = generator.generate_route('厦门', 4, 'xiamen-4days-879')
        if route_data:
            generator.save_route(route_data)
            print(f"[OK] Generated: {route_data['name']}")

        generator.close()

        print("\n[SUCCESS] Fixed all Xiamen routes!")

    except Exception as e:
        print(f"[ERROR] {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    fix_xiamen_routes()
