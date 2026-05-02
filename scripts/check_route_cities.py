"""
检查厦门路线中是否包含其他城市的景点
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.route import Route
from models.attraction import Attraction
import json

def check_xiamen_routes():
    db = SessionLocal()

    try:
        # 获取所有厦门路线
        xiamen_routes = db.query(Route).filter_by(city='厦门').all()
        print(f"厦门路线总数: {len(xiamen_routes)}\n")

        # 获取所有景点，建立名称到城市的映射
        all_attractions = db.query(Attraction).all()
        attraction_city_map = {a.name: a.city for a in all_attractions}

        # 检查每条路线
        for route in xiamen_routes:
            print(f"路线: {route.name} (ID: {route.route_id})")
            print(f"标记城市: {route.city}")

            itinerary = json.loads(route.itinerary)
            has_error = False

            for day in itinerary:
                day_num = day['day']
                attractions_in_day = [a for a in day['activities'] if a['type'] == 'attraction']

                for attr in attractions_in_day:
                    attr_name = attr['name']
                    actual_city = attraction_city_map.get(attr_name, '未知')

                    if actual_city != '厦门':
                        print(f"  [ERROR] Day {day_num}: {attr_name} belongs to {actual_city}")
                        has_error = True
                    else:
                        print(f"  [OK] Day {day_num}: {attr_name} ({actual_city})")

            if not has_error:
                print("  [SUCCESS] All attractions belong to Xiamen")

            print()

    finally:
        db.close()

if __name__ == '__main__':
    check_xiamen_routes()
