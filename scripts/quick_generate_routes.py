"""
快速生成路线脚本
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_generator import RouteGenerator
from models.database import SessionLocal
from models.attraction import Attraction
from models.route import Route

def main():
    print("\n" + "="*60)
    print("路线生成脚本")
    print("="*60)

    # 检查数据
    session = SessionLocal()
    attraction_count = session.query(Attraction).count()
    session.close()

    if attraction_count == 0:
        print("\n数据库中没有景点数据，请先运行数据采集脚本")
        return

    print(f"\n数据库中共有 {attraction_count} 个景点")

    # 生成路线
    cities = ['杭州', '成都', '西安', '厦门', '北京', '上海', '丽江',
              '三亚', '桂林', '青岛', '苏州', '南京', '重庆', '广州', '深圳']
    days_list = [2, 3, 4, 5]

    print(f"\n将为以下城市生成路线: {', '.join(cities)}")
    print(f"天数选项: {', '.join(map(str, days_list))} 天")

    start_time = time.time()
    generator = RouteGenerator()
    success_count = 0

    for city in cities:
        print(f"\n{'='*50}")
        print(f"正在为 {city} 生成路线...")
        print(f"{'='*50}")

        for days in days_list:
            # 每个天数生成2条路线
            for i in range(2):
                route_data = generator.generate_route(city, days)
                if route_data:
                    if generator.save_route(route_data):
                        success_count += 1
                        print(f"  已保存: {route_data['name']}")
                time.sleep(0.2)

    generator.close()

    # 统计
    session = SessionLocal()
    total = session.query(Route).count()
    session.close()

    elapsed = time.time() - start_time

    print("\n" + "="*60)
    print("路线生成完成！")
    print("="*60)
    print(f"成功生成: {success_count} 条路线")
    print(f"数据库中共有: {total} 条路线")
    print(f"耗时: {elapsed:.1f} 秒")
    print("="*60)

if __name__ == "__main__":
    main()
