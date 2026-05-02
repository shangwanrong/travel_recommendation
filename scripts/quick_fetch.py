"""
快速采集脚本 - 采集少量数据用于测试
"""
import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.amap_service import AmapService
from models.database import SessionLocal, init_db
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant
from config import Config

def fetch_data(city: str):
    """采集单个城市的数据"""
    amap = AmapService()
    session = SessionLocal()

    print(f"\n{'='*50}")
    print(f"正在采集 {city} 的数据...")
    print(f"{'='*50}")

    try:
        # 采集景点（1页，20个）
        print("\n1. 采集景点...")
        attractions = amap.search_attractions(city, page=1)
        for attr_data in attractions:
            existing = session.query(Attraction).filter_by(
                name=attr_data['name'], city=city
            ).first()
            if not existing:
                attraction = Attraction(
                    name=attr_data['name'],
                    city=city,
                    province=attr_data['province'],
                    address=attr_data['address'],
                    latitude=attr_data['latitude'],
                    longitude=attr_data['longitude'],
                    phone=attr_data['phone'] if attr_data['phone'] else None,
                    type_code=attr_data['type_code'],
                    source='amap',
                    images=json.dumps([], ensure_ascii=False),
                    tags=json.dumps(['景点'], ensure_ascii=False)
                )
                session.add(attraction)
        session.commit()
        print(f"   完成，获取 {len(attractions)} 个景点")

        # 采集酒店（1页，20个）
        print("\n2. 采集酒店...")
        hotels = amap.search_hotels(city, page=1)
        for hotel_data in hotels:
            existing = session.query(Hotel).filter_by(
                name=hotel_data['name'], city=city
            ).first()
            if not existing:
                hotel = Hotel(
                    name=hotel_data['name'],
                    city=city,
                    province=hotel_data['province'],
                    address=hotel_data['address'],
                    latitude=hotel_data['latitude'],
                    longitude=hotel_data['longitude'],
                    phone=hotel_data['phone'] if hotel_data['phone'] else None,
                    source='amap',
                    images=json.dumps([], ensure_ascii=False),
                    tags=json.dumps(['酒店'], ensure_ascii=False)
                )
                session.add(hotel)
        session.commit()
        print(f"   完成，获取 {len(hotels)} 个酒店")

        # 采集餐厅（1页，20个）
        print("\n3. 采集餐厅...")
        restaurants = amap.search_restaurants(city, page=1)
        for rest_data in restaurants:
            existing = session.query(Restaurant).filter_by(
                name=rest_data['name'], city=city
            ).first()
            if not existing:
                restaurant = Restaurant(
                    name=rest_data['name'],
                    city=city,
                    province=rest_data['province'],
                    address=rest_data['address'],
                    latitude=rest_data['latitude'],
                    longitude=rest_data['longitude'],
                    phone=rest_data['phone'] if rest_data['phone'] else None,
                    source='amap',
                    images=json.dumps([], ensure_ascii=False),
                    tags=json.dumps(['美食'], ensure_ascii=False)
                )
                session.add(restaurant)
        session.commit()
        print(f"   完成，获取 {len(restaurants)} 个餐厅")

        print(f"\n{city} 数据采集完成！")

    except Exception as e:
        print(f"\n采集 {city} 数据时出错: {str(e)}")
        session.rollback()
    finally:
        session.close()

def main():
    print("\n" + "="*60)
    print("快速数据采集脚本")
    print("="*60)

    # 初始化数据库
    print("\n初始化数据库...")
    init_db()

    # 测试API
    amap = AmapService()
    if not amap.test_connection():
        print("\nAPI连接失败，请检查配置")
        return

    # 采集5个城市的数据
    cities = ['杭州', '成都', '西安', '厦门', '北京']

    print(f"\n将采集以下城市的数据: {', '.join(cities)}")
    print("每个城市采集: 20个景点 + 20个酒店 + 20个餐厅")

    start_time = time.time()

    for i, city in enumerate(cities, 1):
        print(f"\n\n进度: [{i}/{len(cities)}]")
        fetch_data(city)
        time.sleep(1)

    # 统计
    session = SessionLocal()
    stats = {
        'attractions': session.query(Attraction).count(),
        'hotels': session.query(Hotel).count(),
        'restaurants': session.query(Restaurant).count()
    }
    session.close()

    elapsed = time.time() - start_time

    print("\n" + "="*60)
    print("数据采集完成！")
    print("="*60)
    print(f"景点: {stats['attractions']} 个")
    print(f"酒店: {stats['hotels']} 个")
    print(f"餐厅: {stats['restaurants']} 个")
    print(f"耗时: {elapsed:.1f} 秒")
    print("="*60)

if __name__ == "__main__":
    main()
