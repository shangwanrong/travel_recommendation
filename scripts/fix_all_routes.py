"""
修复所有包含跨城市景点的路线
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.route import Route
from models.attraction import Attraction
from services.data_generator import RouteGenerator
import json

def fix_all_routes():
    db = SessionLocal()

    try:
        # 获取所有路线和景点
        all_routes = db.query(Route).all()
        all_attractions = db.query(Attraction).all()
        attraction_city_map = {a.name: a.city for a in all_attractions}

        # 找出所有有问题的路线
        problem_routes = []

        for route in all_routes:
            itinerary = json.loads(route.itinerary)
            has_error = False

            for day in itinerary:
                attractions_in_day = [a for a in day['activities'] if a['type'] == 'attraction']

                for attr in attractions_in_day:
                    attr_name = attr['name']
                    actual_city = attraction_city_map.get(attr_name, 'Unknown')

                    if actual_city != route.city:
                        has_error = True
                        break

                if has_error:
                    break

            if has_error:
                problem_routes.append(route)

        print(f"Found {len(problem_routes)} problematic routes\n")

        if len(problem_routes) == 0:
            print("[SUCCESS] All routes are correct!")
            return

        # 删除并重新生成有问题的路线
        generator = RouteGenerator()

        for route in problem_routes:
            print(f"Fixing: {route.name} ({route.route_id})")

            # 保存路线信息
            city = route.city
            days = route.days
            route_id = route.route_id

            # 删除旧路线
            db.delete(route)
            db.commit()

            # 重新生成
            route_data = generator.generate_route(city, days, route_id)
            if route_data:
                generator.save_route(route_data)
                print(f"  [OK] Regenerated: {route_data['name']}")
            else:
                print(f"  [ERROR] Failed to regenerate")

        generator.close()

        print(f"\n[SUCCESS] Fixed {len(problem_routes)} routes!")

    except Exception as e:
        print(f"[ERROR] {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    fix_all_routes()
