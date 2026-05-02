"""
检查所有城市的路线是否包含其他城市的景点
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.route import Route
from models.attraction import Attraction
import json

def check_all_routes():
    db = SessionLocal()

    try:
        # 获取所有路线
        all_routes = db.query(Route).all()
        print(f"Total routes: {len(all_routes)}\n")

        # 获取所有景点，建立名称到城市的映射
        all_attractions = db.query(Attraction).all()
        attraction_city_map = {a.name: a.city for a in all_attractions}

        # 按城市分组检查
        cities = set(r.city for r in all_routes)
        total_errors = 0

        for city in sorted(cities):
            city_routes = [r for r in all_routes if r.city == city]
            print(f"=== {city} ({len(city_routes)} routes) ===")

            city_errors = 0
            for route in city_routes:
                itinerary = json.loads(route.itinerary)
                route_errors = []

                for day in itinerary:
                    attractions_in_day = [a for a in day['activities'] if a['type'] == 'attraction']

                    for attr in attractions_in_day:
                        attr_name = attr['name']
                        actual_city = attraction_city_map.get(attr_name, 'Unknown')

                        if actual_city != city:
                            route_errors.append(f"Day {day['day']}: {attr_name} ({actual_city})")

                if route_errors:
                    print(f"  [ERROR] {route.name} ({route.route_id}):")
                    for error in route_errors:
                        print(f"    - {error}")
                    city_errors += 1

            if city_errors == 0:
                print(f"  [OK] All routes are correct")
            else:
                print(f"  [WARNING] {city_errors} routes have errors")
                total_errors += city_errors

            print()

        print(f"=== Summary ===")
        print(f"Total routes checked: {len(all_routes)}")
        print(f"Routes with errors: {total_errors}")

        if total_errors == 0:
            print("[SUCCESS] All routes are correct!")
        else:
            print(f"[WARNING] Found {total_errors} routes with cross-city attractions")

    finally:
        db.close()

if __name__ == '__main__':
    check_all_routes()
