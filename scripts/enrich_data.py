"""
数据增强脚本
为景点、酒店、餐厅补充合理的描述、价格、评分等信息
基于真实数据生成，不依赖外部爬虫
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import json
from models.database import SessionLocal
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant


class DataEnricher:
    """数据增强器"""

    def __init__(self):
        self.session = SessionLocal()

        # 景点类型描述模板
        self.attraction_templates = {
            '风景名胜': [
                '这里风景秀丽，是{city}著名的旅游胜地。四季景色各异，春有繁花，夏有绿荫，秋有红叶，冬有雪景。',
                '位于{city}的标志性景点，以其独特的自然风光和深厚的文化底蕴吸引着众多游客。',
                '集自然美景与人文景观于一体，是{city}不可错过的旅游目的地。'
            ],
            '公园': [
                '市民休闲的好去处，环境优美，设施完善。适合散步、健身、亲子活动。',
                '绿树成荫，鸟语花香，是城市中的一片绿洲。周末常有市民在此休闲娱乐。',
                '占地广阔的城市公园，拥有湖泊、草坪、游乐设施等，是家庭出游的理想选择。'
            ],
            '历史遗迹': [
                '历史悠久，文化底蕴深厚。见证了{city}的发展变迁，是了解当地历史文化的重要窗口。',
                '保存完好的历史建筑，具有重要的历史和艺术价值。',
                '承载着丰富的历史故事，每一砖一瓦都诉说着过往的辉煌。'
            ]
        }

        # 酒店描述模板
        self.hotel_templates = [
            '地理位置优越，交通便利。客房宽敞舒适，设施齐全。提供优质的服务，是商务出行和休闲度假的理想选择。',
            '现代化的酒店设施，温馨舒适的住宿环境。周边配套完善，购物餐饮便利。',
            '精心设计的客房，注重细节与品质。提供24小时热水、免费WiFi等基础设施。',
            '性价比高，服务周到。适合家庭出游和商务差旅。'
        ]

        # 餐厅描述模板
        self.restaurant_templates = [
            '地道的{city}美食，食材新鲜，味道正宗。环境整洁，服务热情。',
            '人气餐厅，招牌菜品深受食客喜爱。价格实惠，分量足。',
            '特色餐饮，融合传统与创新。适合朋友聚餐、家庭聚会。',
            '口碑良好的老字号，传承经典味道。是品尝当地美食的好去处。'
        ]

    def enrich_attractions(self, limit=None):
        """补充景点信息"""
        print("\n" + "="*60)
        print("补充景点信息")
        print("="*60)

        query = self.session.query(Attraction).filter(
            (Attraction.description == None) | (Attraction.description == '')
        )

        if limit:
            query = query.limit(limit)

        attractions = query.all()

        if not attractions:
            print("\n所有景点都已有描述")
            return

        print(f"\n找到 {len(attractions)} 个需要补充的景点")

        for i, attraction in enumerate(attractions, 1):
            print(f"\n[{i}/{len(attractions)}] {attraction.name}")

            try:
                # 生成描述
                template = random.choice(self.attraction_templates['风景名胜'])
                description = template.format(city=attraction.city)
                attraction.description = description

                # 门票价格：不再随机生成，保留真实数据
                # ticket_price 由 update_ticket_prices.py 脚本统一管理

                # 生成评分（如果没有）
                if not attraction.rating:
                    attraction.rating = round(random.uniform(4.0, 4.8), 1)

                # 补充标签
                existing_tags = json.loads(attraction.tags) if attraction.tags else []
                if not existing_tags:
                    tags = ['景点', '旅游', attraction.city]
                    attraction.tags = json.dumps(tags, ensure_ascii=False)

                self.session.commit()
                print(f"  已更新: 描述、门票({attraction.ticket_price}元)、评分({attraction.rating})")

            except Exception as e:
                print(f"  更新失败: {str(e)}")
                self.session.rollback()

        print("\n景点信息补充完成！")

    def enrich_hotels(self, limit=None):
        """补充酒店信息"""
        print("\n" + "="*60)
        print("补充酒店信息")
        print("="*60)

        query = self.session.query(Hotel).filter(
            (Hotel.description == None) | (Hotel.description == '')
        )

        if limit:
            query = query.limit(limit)

        hotels = query.all()

        if not hotels:
            print("\n所有酒店都已有描述")
            return

        print(f"\n找到 {len(hotels)} 个需要补充的酒店")

        for i, hotel in enumerate(hotels, 1):
            print(f"\n[{i}/{len(hotels)}] {hotel.name}")

            try:
                # 生成描述
                description = random.choice(self.hotel_templates)
                hotel.description = description

                # 生成价格区间
                if not hotel.price_range:
                    base_price = random.choice([200, 250, 300, 350, 400, 500])
                    hotel.price_range = f"{base_price}-{base_price + 200}元"

                # 生成评分
                if not hotel.rating:
                    hotel.rating = round(random.uniform(4.0, 4.7), 1)

                # 生成星级
                if not hotel.star_level:
                    hotel.star_level = random.choice(['经济型', '舒适型', '三星级', '四星级'])

                # 补充标签
                existing_tags = json.loads(hotel.tags) if hotel.tags else []
                if not existing_tags:
                    tags = ['酒店', '住宿', hotel.city]
                    hotel.tags = json.dumps(tags, ensure_ascii=False)

                self.session.commit()
                print(f"  已更新: 描述、价格({hotel.price_range})、评分({hotel.rating})、星级({hotel.star_level})")

            except Exception as e:
                print(f"  更新失败: {str(e)}")
                self.session.rollback()

        print("\n酒店信息补充完成！")

    def enrich_restaurants(self, limit=None):
        """补充餐厅信息"""
        print("\n" + "="*60)
        print("补充餐厅信息")
        print("="*60)

        query = self.session.query(Restaurant).filter(
            (Restaurant.description == None) | (Restaurant.description == '')
        )

        if limit:
            query = query.limit(limit)

        restaurants = query.all()

        if not restaurants:
            print("\n所有餐厅都已有描述")
            return

        print(f"\n找到 {len(restaurants)} 个需要补充的餐厅")

        for i, restaurant in enumerate(restaurants, 1):
            try:
                print(f"\n[{i}/{len(restaurants)}] {restaurant.name}")
            except UnicodeEncodeError:
                print(f"\n[{i}/{len(restaurants)}] (餐厅名称包含特殊字符)")

            try:
                # 生成描述
                template = random.choice(self.restaurant_templates)
                description = template.format(city=restaurant.city)
                restaurant.description = description

                # 生成人均消费
                if not restaurant.avg_price:
                    restaurant.avg_price = random.choice([30, 40, 50, 60, 80, 100, 120, 150])

                # 生成评分
                if not restaurant.rating:
                    restaurant.rating = round(random.uniform(4.0, 4.7), 1)

                # 生成菜系类型
                if not restaurant.cuisine_type:
                    cuisines = ['中餐', '川菜', '粤菜', '湘菜', '本帮菜', '火锅', '小吃']
                    restaurant.cuisine_type = random.choice(cuisines)

                # 补充标签
                existing_tags = json.loads(restaurant.tags) if restaurant.tags else []
                if not existing_tags:
                    tags = ['美食', restaurant.cuisine_type, restaurant.city]
                    restaurant.tags = json.dumps(tags, ensure_ascii=False)

                self.session.commit()
                print(f"  已更新: 描述、人均({restaurant.avg_price}元)、评分({restaurant.rating})、菜系({restaurant.cuisine_type})")

            except Exception as e:
                print(f"  更新失败: {str(e)}")
                self.session.rollback()

        print("\n餐厅信息补充完成！")

    def close(self):
        """关闭数据库连接"""
        self.session.close()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("数据增强工具")
    print("="*60)
    print("\n此工具将为数据库中的景点、酒店、餐厅补充以下信息：")
    print("- 描述文字")
    print("- 价格信息")
    print("- 评分")
    print("- 标签")
    print("\n注意：生成的数据基于合理的市场行情，仅供展示使用")

    input("\n按回车键开始...")

    enricher = DataEnricher()

    try:
        # 补充所有数据
        enricher.enrich_attractions()
        enricher.enrich_hotels()
        enricher.enrich_restaurants()

        print("\n" + "="*60)
        print("数据增强完成！")
        print("="*60)

        # 统计
        session = SessionLocal()
        stats = {
            'attractions': session.query(Attraction).filter(Attraction.description != None).count(),
            'hotels': session.query(Hotel).filter(Hotel.description != None).count(),
            'restaurants': session.query(Restaurant).filter(Restaurant.description != None).count()
        }
        session.close()

        print(f"\n当前数据统计：")
        print(f"  景点（有描述）: {stats['attractions']} 个")
        print(f"  酒店（有描述）: {stats['hotels']} 个")
        print(f"  餐厅（有描述）: {stats['restaurants']} 个")

    finally:
        enricher.close()


if __name__ == "__main__":
    main()
