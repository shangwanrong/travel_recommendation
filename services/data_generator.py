"""
智能路线生成器
基于真实景点数据生成合理的旅游路线
"""
import sys
import os
import random
import json
from typing import List, Dict, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant
from models.route import Route

try:
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("⚠️  geopy未安装，将使用简化的距离计算")

class RouteGenerator:
    """路线生成器"""

    def __init__(self):
        self.session = SessionLocal()

    def generate_route(self, city: str, days: int, route_id: str = None) -> Optional[Dict]:
        """
        生成路线

        Args:
            city: 城市名称
            days: 天数
            route_id: 路线ID（可选）

        Returns:
            路线数据字典
        """

        # 1. 获取景点数据
        attractions = self.session.query(Attraction).filter_by(city=city).all()
        if len(attractions) < days * 2:
            print(f"{city} 景点数据不足（需要至少 {days*2} 个，实际 {len(attractions)} 个）")
            return None

        # 2. 获取酒店和餐厅
        hotels = self.session.query(Hotel).filter_by(city=city).all()
        restaurants = self.session.query(Restaurant).filter_by(city=city).all()

        # 3. 选择景点
        selected_attractions = self._select_attractions(attractions, days)

        # 4. 优化顺序
        optimized_attractions = self._optimize_route(selected_attractions)

        # 5. 生成详细行程
        itinerary = self._generate_itinerary(
            optimized_attractions,
            hotels,
            restaurants,
            days
        )

        # 6. 计算价格
        price = self._calculate_price(itinerary, days)

        # 7. 生成路线名称和描述
        route_name = self._generate_route_name(city, days, optimized_attractions)
        description = self._generate_description(city, days, optimized_attractions)
        tags = self._generate_tags(optimized_attractions)

        # 8. 生成路线ID
        if not route_id:
            city_code = self._get_city_code(city)
            route_id = f"{city_code}-{days}days-{random.randint(100, 999):03d}"

        route_data = {
            'route_id': route_id,
            'name': route_name,
            'city': city,
            'city_id': self._get_city_code(city),
            'days': days,
            'description': description,
            'price_range': f"{price['min']}-{price['max']}元",
            'rating': round(random.uniform(4.3, 4.9), 1),
            'popularity': random.randint(75, 95),
            'tags': tags,
            'itinerary': itinerary,
            'cover_image': f'https://picsum.photos/seed/{route_id}/800/600'
        }

        print(f"路线生成完成: {route_name}")
        return route_data

    def _select_attractions(self, attractions: List[Attraction], days: int) -> List[Attraction]:
        """选择景点（每天2-3个）"""
        count = days * 2 + random.randint(0, days)
        count = min(count, len(attractions))
        return random.sample(attractions, count)

    def _optimize_route(self, attractions: List[Attraction]) -> List[Attraction]:
        """
        优化路线顺序 - 改进的贪心算法
        策略：从地理中心开始，逐步向外扩展，避免来回跳跃
        """
        if not attractions or len(attractions) <= 1:
            return attractions

        if not GEOPY_AVAILABLE:
            # 如果geopy不可用，随机打乱
            random.shuffle(attractions)
            return attractions

        # 1. 计算所有景点的地理中心
        center_lat = sum(a.latitude for a in attractions) / len(attractions)
        center_lng = sum(a.longitude for a in attractions) / len(attractions)

        # 2. 找到离中心最近的景点作为起点
        start_attraction = min(attractions, key=lambda a: geodesic(
            (center_lat, center_lng),
            (a.latitude, a.longitude)
        ).km)

        # 3. 使用改进的最近邻算法
        optimized = [start_attraction]
        remaining = [a for a in attractions if a != start_attraction]

        while remaining:
            current = optimized[-1]

            # 找到距离当前位置最近的3个景点
            nearest_candidates = sorted(remaining, key=lambda a: geodesic(
                (current.latitude, current.longitude),
                (a.latitude, a.longitude)
            ).km)[:min(3, len(remaining))]

            # 从这3个候选中选择一个（优先选择最近的，但有20%概率选择次近的，增加多样性）
            if len(nearest_candidates) > 1 and random.random() < 0.2:
                nearest = nearest_candidates[1]
            else:
                nearest = nearest_candidates[0]

            optimized.append(nearest)
            remaining.remove(nearest)

        return optimized

    def _generate_itinerary(
        self,
        attractions: List[Attraction],
        hotels: List[Hotel],
        restaurants: List[Restaurant],
        days: int
    ) -> List[Dict]:
        """生成详细行程"""
        itinerary = []
        attractions_per_day = len(attractions) // days

        for day in range(1, days + 1):
            start_idx = (day - 1) * attractions_per_day
            end_idx = start_idx + attractions_per_day if day < days else len(attractions)
            day_attractions = attractions[start_idx:end_idx]

            activities = []
            time_slot = 9  # 从9点开始

            # 添加景点
            for i, attr in enumerate(day_attractions):
                activities.append({
                    'time': f"{time_slot:02d}:00",
                    'type': 'attraction',
                    'name': attr.name,
                    'description': attr.description or f'游览{attr.name}，感受当地文化魅力',
                    'latitude': attr.latitude,
                    'longitude': attr.longitude
                })
                time_slot += 3  # 每个景点3小时

                # 中午添加餐饮
                if i == len(day_attractions) // 2 and restaurants:
                    restaurant = random.choice(restaurants)
                    activities.append({
                        'time': f"{time_slot:02d}:00",
                        'type': 'dining',
                        'name': restaurant.name,
                        'description': f'品尝当地特色美食',
                        'latitude': restaurant.latitude,
                        'longitude': restaurant.longitude
                    })
                    time_slot += 1

            # 晚上添加酒店（除了最后一天）
            if day < days and hotels:
                hotel = random.choice(hotels)
                activities.append({
                    'time': '18:00',
                    'type': 'hotel',
                    'name': hotel.name,
                    'description': '入住酒店，休息放松',
                    'latitude': hotel.latitude,
                    'longitude': hotel.longitude
                })

            itinerary.append({
                'day': day,
                'activities': activities
            })

        return itinerary

    def _calculate_price(self, itinerary: List[Dict], days: int) -> Dict:
        """计算价格"""
        # 基础价格
        base_price = days * 200

        # 景点门票
        ticket_price = len([a for day in itinerary for a in day['activities'] if a['type'] == 'attraction']) * 50

        # 住宿
        hotel_price = (days - 1) * 300

        # 餐饮
        food_price = days * 150

        min_price = int(base_price + ticket_price + hotel_price + food_price)
        max_price = int(min_price * 1.5)

        return {'min': min_price, 'max': max_price}

    def _generate_route_name(self, city: str, days: int, attractions: List[Attraction]) -> str:
        """生成路线名称"""
        themes = ['深度游', '精华游', '文化之旅', '休闲游', '经典游']
        theme = random.choice(themes)
        return f"{city}{days}天{days-1}晚{theme}"

    def _generate_description(self, city: str, days: int, attractions: List[Attraction]) -> str:
        """生成路线描述"""
        top_attractions = [a.name for a in attractions[:3]]
        attractions_str = '、'.join(top_attractions)
        return f"探索{city}的魅力，游览{attractions_str}等著名景点，体验当地文化与美食，享受{days}天{days-1}晚的完美旅程。"

    def _generate_tags(self, attractions: List[Attraction]) -> List[str]:
        """生成标签"""
        all_tags = ['文化古迹', '自然风光', '美食之旅', '休闲度假', '亲子游', '摄影天堂']
        return random.sample(all_tags, k=min(3, len(all_tags)))

    def _get_city_code(self, city: str) -> str:
        """获取城市代码"""
        city_codes = {
            '北京': 'beijing', '上海': 'shanghai', '杭州': 'hangzhou',
            '成都': 'chengdu', '西安': 'xian', '厦门': 'xiamen',
            '丽江': 'lijiang', '三亚': 'sanya', '桂林': 'guilin',
            '青岛': 'qingdao', '苏州': 'suzhou', '南京': 'nanjing',
            '重庆': 'chongqing', '广州': 'guangzhou', '深圳': 'shenzhen'
        }
        return city_codes.get(city, 'city')

    def save_route(self, route_data: Dict) -> bool:
        """保存路线到数据库"""
        try:
            route = Route(
                route_id=route_data['route_id'],
                name=route_data['name'],
                city=route_data['city'],
                city_id=route_data['city_id'],
                days=route_data['days'],
                description=route_data['description'],
                price_range=route_data['price_range'],
                cover_image=route_data['cover_image'],
                rating=route_data['rating'],
                popularity=route_data['popularity'],
                tags=json.dumps(route_data['tags'], ensure_ascii=False),
                itinerary=json.dumps(route_data['itinerary'], ensure_ascii=False)
            )
            self.session.add(route)
            self.session.commit()
            return True
        except Exception as e:
            print(f"保存路线失败: {str(e)}")
            self.session.rollback()
            return False

    def close(self):
        """关闭数据库连接"""
        self.session.close()
