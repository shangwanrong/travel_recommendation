"""
强制修复最后一条有问题的路线
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, engine
from models.route import Route
from models.attraction import Attraction
from services.data_generator import RouteGenerator
import json

def force_fix_route():
    # 创建新的数据库会话
    db = SessionLocal()

    try:
        # 删除有问题的路线
        route = db.query(Route).filter_by(route_id='hangzhou-4days-357').first()
        if route:
            print(f"Deleting: {route.name} ({route.route_id})")
            db.delete(route)
            db.commit()
            print("[OK] Deleted")

        # 关闭旧会话
        db.close()

        # 创建新的生成器（新会话）
        generator = RouteGenerator()

        # 验证杭州景点
        hangzhou_attrs = generator.session.query(Attraction).filter_by(city='杭州').all()
        print(f"\nHangzhou attractions: {len(hangzhou_attrs)}")
        print("Sample attractions:")
        for a in hangzhou_attrs[:5]:
            print(f"  - {a.name} ({a.city})")

        # 检查是否有景山
        jingshan = [a for a in hangzhou_attrs if '景山' in a.name]
        if jingshan:
            print(f"\n[WARNING] Found Jingshan in Hangzhou: {[a.name for a in jingshan]}")
        else:
            print("\n[OK] No Jingshan in Hangzhou attractions")

        # 重新生成路线
        print("\nRegenerating route...")
        route_data = generator.generate_route('杭州', 4, 'hangzhou-4days-357')

        if route_data:
            # 验证生成的路线
            print("\nVerifying generated route...")
            itinerary = route_data['itinerary']
            all_correct = True

            for day in itinerary:
                attractions_in_day = [a for a in day['activities'] if a['type'] == 'attraction']
                for attr in attractions_in_day:
                    attr_name = attr['name']
                    # 在数据库中查找这个景点
                    db_attr = generator.session.query(Attraction).filter_by(name=attr_name).first()
                    if db_attr and db_attr.city != '杭州':
                        print(f"  [ERROR] Day {day['day']}: {attr_name} belongs to {db_attr.city}")
                        all_correct = False

            if all_correct:
                print("[OK] All attractions are correct, saving...")
                generator.save_route(route_data)
                print(f"[SUCCESS] Generated and saved: {route_data['name']}")
            else:
                print("[ERROR] Generated route still has errors, not saving")

        generator.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        if db:
            db.close()

if __name__ == '__main__':
    force_fix_route()
