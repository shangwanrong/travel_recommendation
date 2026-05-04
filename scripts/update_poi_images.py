"""
更新POI图片路径到数据库
将static/images/下的图片关联到对应的POI
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant

def update_attraction_images():
    """更新景点图片"""
    db = SessionLocal()

    # 图片映射（根据实际文件名）
    image_map = {
        '西湖': ['/static/images/attractions/xihu.jpg'],
        '雷峰塔': ['/static/images/attractions/leifengta.jpg'],
        '宋城': ['/static/images/attractions/songchengguzhen.jpg'],
        '灵隐寺': ['/static/images/attractions/xihu.jpg'],  # 使用通用图片
        '千岛湖': ['/static/images/attractions/xihu.jpg'],

        '兵马俑': ['/static/images/attractions/terracotta.jpg'],
        '大雁塔': ['/static/images/attractions/xian.jpg'],
        '华清池': ['/static/images/attractions/xian.jpg'],
        '钟楼': ['/static/images/attractions/xian.jpg'],
        '城墙': ['/static/images/attractions/xian.jpg'],

        '宽窄巷子': ['/static/images/attractions/chengdu_panda.jpg'],
        '锦里': ['/static/images/attractions/chengdu_panda.jpg'],
        '大熊猫基地': ['/static/images/attractions/chengdu_panda.jpg'],
        '武侯祠': ['/static/images/attractions/chengdu_panda.jpg'],
        '都江堰': ['/static/images/attractions/chengdu_panda.jpg'],

        '鼓浪屿': ['/static/images/attractions/gulangyu.jpg'],
        '南普陀寺': ['/static/images/attractions/gulangyu.jpg'],
        '曾厝垵': ['/static/images/attractions/gulangyu.jpg'],
        '环岛路': ['/static/images/attractions/gulangyu.jpg'],
        '厦门大学': ['/static/images/attractions/gulangyu.jpg'],

        '故宫': ['/static/images/attractions/forbidden_city.jpg'],
        '天安门': ['/static/images/attractions/beijing.jpg'],
        '长城': ['/static/images/attractions/beijing.jpg'],
        '颐和园': ['/static/images/attractions/beijing.jpg'],
        '天坛': ['/static/images/attractions/beijing.jpg'],
    }

    try:
        attractions = db.query(Attraction).all()
        updated = 0

        for attraction in attractions:
            # 尝试精确匹配
            if attraction.name in image_map:
                attraction.images = json.dumps(image_map[attraction.name])
                updated += 1
            else:
                # 模糊匹配
                for key in image_map:
                    if key in attraction.name or attraction.name in key:
                        attraction.images = json.dumps(image_map[key])
                        updated += 1
                        break
                else:
                    # 使用城市默认图片
                    city_images = {
                        '杭州': ['/static/images/attractions/xihu.jpg'],
                        '西安': ['/static/images/attractions/xian.jpg'],
                        '成都': ['/static/images/attractions/chengdu_panda.jpg'],
                        '厦门': ['/static/images/attractions/gulangyu.jpg'],
                        '北京': ['/static/images/attractions/beijing.jpg'],
                    }
                    if attraction.city in city_images:
                        attraction.images = json.dumps(city_images[attraction.city])
                        updated += 1

        db.commit()
        print(f"[OK] 更新了 {updated} 个景点的图片")

    except Exception as e:
        print(f"[ERROR] 更新景点图片失败: {e}")
        db.rollback()
    finally:
        db.close()

def update_hotel_images():
    """更新酒店图片"""
    db = SessionLocal()

    # 使用占位图片
    default_images = [
        'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800',
        'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800'
    ]

    try:
        hotels = db.query(Hotel).all()
        for hotel in hotels:
            hotel.images = json.dumps(default_images)

        db.commit()
        print(f"[OK] 更新了 {len(hotels)} 个酒店的图片")

    except Exception as e:
        print(f"[ERROR] 更新酒店图片失败: {e}")
        db.rollback()
    finally:
        db.close()

def update_restaurant_images():
    """更新餐厅图片"""
    db = SessionLocal()

    # 使用占位图片
    default_images = [
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800',
        'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800'
    ]

    try:
        restaurants = db.query(Restaurant).all()
        for restaurant in restaurants:
            restaurant.images = json.dumps(default_images)

        db.commit()
        print(f"[OK] 更新了 {len(restaurants)} 个餐厅的图片")

    except Exception as e:
        print(f"[ERROR] 更新餐厅图片失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    print("Starting POI image update...")
    print("\n1. Updating attraction images")
    update_attraction_images()

    print("\n2. Updating hotel images")
    update_hotel_images()

    print("\n3. Updating restaurant images")
    update_restaurant_images()

    print("\n[SUCCESS] All images updated!")
