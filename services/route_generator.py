"""
路线生成器 - 核心算法模块
根据用户偏好、城市、预算、天数等参数智能生成旅游路线

核心算法：
1. POI筛选：根据偏好和预算筛选景点/酒店/餐厅
2. 方向性排序：按照地理方向（如自北向南）排列景点，避免折返
3. 住宿优化：住宿位置靠近当日游玩区域中心
4. 时间差异化：根据景点类型分配不同游玩时长
5. 预算分配：合理分配门票、餐饮、住宿、交通预算
"""
import math
import random
from collections import defaultdict
from models.database import SessionLocal
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant


class RouteGenerator:
    """路线生成器"""

    # 节奏对应的每日景点数量
    PACE_DAILY_COUNT = {
        'relaxed': 3,      # 悠闲：2-3个
        'moderate': 4,     # 适中：3-4个
        'intensive': 5     # 紧凑：4-5个
    }

    # 每日最大游玩时间（分钟）
    DAILY_MAX_TIME = {
        'relaxed': 480,    # 8小时
        'moderate': 600,   # 10小时
        'intensive': 720   # 12小时
    }

    # 偏好对应的景点分类权重
    PREFERENCE_WEIGHTS = {
        'scenery': {'scenery': 5, 'entertainment': 2, 'historical': 2, 'religious': 1, 'shopping': 0, 'leisure': 1, 'other': 1},
        'historical': {'scenery': 2, 'entertainment': 1, 'historical': 5, 'religious': 3, 'shopping': 1, 'leisure': 1, 'other': 1},
        'entertainment': {'scenery': 2, 'entertainment': 5, 'historical': 1, 'religious': 0, 'shopping': 2, 'leisure': 3, 'other': 1},
        'balanced': {'scenery': 3, 'entertainment': 3, 'historical': 3, 'religious': 1, 'shopping': 1, 'leisure': 2, 'other': 1}
    }

    # 交通方式对应的每日交通费用估算
    TRANSPORT_DAILY_COST = {
        'self-driving': 80,        # 油费+停车
        'public-transport': 30     # 公交/地铁
    }

    # 住宿预算比例
    HOTEL_BUDGET_RATIO = 0.35
    # 餐饮预算比例
    FOOD_BUDGET_RATIO = 0.25
    # 门票预算比例
    TICKET_BUDGET_RATIO = 0.25
    # 交通预算比例
    TRANSPORT_BUDGET_RATIO = 0.15

    def __init__(self):
        self.db = SessionLocal()

    def __del__(self):
        try:
            self.db.close()
        except:
            pass

    def generate_routes(self, preference, pace, city_id, city_name, days, budget, transport):
        """
        生成定制路线的主入口
        
        参数:
            preference: 偏好类型 (scenery/historical/entertainment/balanced)
            pace: 节奏 (relaxed/moderate/intensive)
            city_id: 城市ID
            city_name: 城市名称
            days: 天数
            budget: 预算（元）
            transport: 交通方式
            
        返回:
            list: 3-4个备选路线方案
        """
        try:
            # 1. 获取城市所有POI
            attractions = self._get_attractions(city_name)
            hotels = self._get_hotels(city_name)
            restaurants = self._get_restaurants(city_name)

            if not attractions:
                return []

            # 2. 根据偏好筛选和排序景点
            weighted_attractions = self._weight_attractions(attractions, preference)

            # 3. 计算每日预算分配
            daily_budget = budget / days
            hotel_budget = daily_budget * self.HOTEL_BUDGET_RATIO
            food_budget = daily_budget * self.FOOD_BUDGET_RATIO
            ticket_budget = daily_budget * self.TICKET_BUDGET_RATIO
            transport_daily = daily_budget * self.TRANSPORT_BUDGET_RATIO

            # 4. 计算每日景点数量
            daily_count = self.PACE_DAILY_COUNT.get(pace, 4)
            daily_max_time = self.DAILY_MAX_TIME.get(pace, 480)

            # 5. 生成多个备选方案
            preference_name_map = {
                'scenery': '风光', 'historical': '人文', 'entertainment': '娱乐', 'balanced': '精选'
            }
            
            # 方案配置：每个方案有不同的偏好侧重和景点密度
            route_configs = [
                {
                    'name': f'{city_name}{preference_name_map.get(preference, "精选")}{days}日游',
                    'pref_override': None,      # 使用用户原始偏好
                    'count_offset': 0,          # 标准景点数
                    'desc_suffix': ''
                },
                {
                    'name': f'{city_name}深度慢游{days}日游',
                    'pref_override': self._shift_preference(preference, -1),  # 偏好向相邻类型偏移
                    'count_offset': -1,         # 更少景点更深入
                    'desc_suffix': '，细细品味每个景点'
                },
                {
                    'name': f'{city_name}全景打卡{days}日游',
                    'pref_override': self._shift_preference(preference, 1),
                    'count_offset': 1,          # 更多景点更丰富
                    'desc_suffix': '，不走回头路'
                }
            ]

            # 生成多个差异化方案
            routes = []
            for i, config in enumerate(route_configs):
                # 根据方案配置调整偏好
                effective_pref = config['pref_override'] or preference
                effective_count = daily_count + config['count_offset']
                
                # 重新按偏好的变体加权排序景点
                variant_attractions = self._weight_attractions(attractions, effective_pref)
                
                route = self._generate_single_route(
                    weighted_attractions=variant_attractions,
                    hotels=hotels,
                    restaurants=restaurants,
                    city_name=city_name,
                    city_id=city_id,
                    days=days,
                    daily_count=effective_count,
                    daily_max_time=daily_max_time,
                    hotel_budget=hotel_budget,
                    food_budget=food_budget,
                    ticket_budget=ticket_budget,
                    transport=transport,
                    route_name=config['name']
                )
                if route:
                    routes.append(route)

            return routes

        except Exception as e:
            print(f"生成路线失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_attractions(self, city_name):
        """获取城市景点"""
        return self.db.query(Attraction).filter(
            Attraction.city == city_name,
            Attraction.latitude.isnot(None),
            Attraction.longitude.isnot(None)
        ).all()

    def _get_hotels(self, city_name):
        """获取城市酒店"""
        return self.db.query(Hotel).filter(
            Hotel.city == city_name,
            Hotel.latitude.isnot(None),
            Hotel.longitude.isnot(None)
        ).all()

    def _get_restaurants(self, city_name):
        """获取城市餐厅"""
        return self.db.query(Restaurant).filter(
            Restaurant.city == city_name,
            Restaurant.latitude.isnot(None),
            Restaurant.longitude.isnot(None)
        ).all()

    def _weight_attractions(self, attractions, preference):
        """根据偏好给景点加权排序"""
        weights = self.PREFERENCE_WEIGHTS.get(preference, self.PREFERENCE_WEIGHTS['balanced'])

        scored = []
        for a in attractions:
            # 偏好权重
            cat = a.category or 'other'
            pref_score = weights.get(cat, 1)

            # 评分加成（4.5以上额外加分）
            rating_score = (a.rating or 4.0) / 5.0

            # 综合得分
            total_score = pref_score * 0.6 + rating_score * 0.4

            scored.append({
                'attraction': a,
                'score': total_score,
                'category': cat
            })

        # 按得分降序排序
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored

    def _shift_preference(self, preference, direction):
        """偏好偏移，用于生成差异化方案"""
        pref_cycle = ['scenery', 'historical', 'entertainment', 'balanced']
        pref_idx = {'scenery': 0, 'historical': 1, 'entertainment': 2, 'balanced': 3}
        current = pref_idx.get(preference, 3)
        shifted = (current + direction) % len(pref_cycle)
        return pref_cycle[shifted]

    def _generate_single_route(self, weighted_attractions, hotels, restaurants,
                                city_name, city_id, days, daily_count, daily_max_time,
                                hotel_budget, food_budget, ticket_budget,
                                transport, route_name):
        """
        生成单个路线方案
        
        核心算法：
        1. 取top-N景点
        2. 按方向性排序（自北向南或自南向北）
        3. 分配到每天
        4. 为每天选择住宿和餐饮
        5. 计算预算
        """
        # 确保daily_count合理
        daily_count = max(2, min(6, daily_count))
        total_needed = days * daily_count

        # 选取景点
        selected = weighted_attractions[:total_needed + 5]  # 多选几个备用

        if not selected:
            return None

        # 方向性排序
        sorted_pois = self._directional_sort(selected)

        # 分配到每天
        daily_plans = self._allocate_daily(sorted_pois, days, daily_count, daily_max_time, ticket_budget)

        # 为每天安排住宿和餐饮
        for day_plan in daily_plans:
            day_num = day_plan['day']
            day_pois = day_plan['attractions']

            if not day_pois:
                continue

            # 计算当日游玩区域中心
            center_lat, center_lng = self._calculate_center(day_pois)

            # 选择住宿
            hotel = self._select_hotel(hotels, center_lat, center_lng, hotel_budget)
            day_plan['hotel'] = hotel

            # 选择餐饮
            meals = self._select_restaurants(restaurants, day_pois, food_budget)
            day_plan['meals'] = meals

            # 计算当日交通
            transport_info = self._estimate_transport(day_pois, transport)
            day_plan['transport'] = transport_info

            # 计算当日费用
            day_cost = self._calculate_day_cost(day_plan, transport)
            day_plan['estimated_cost'] = day_cost

        # 计算路线总预算
        total_cost = sum(d.get('estimated_cost', 0) for d in daily_plans)

        # 构建路线数据
        route = {
            'name': route_name,
            'city': city_name,
            'city_id': city_id,
            'days': days,
            'transport_mode': transport,
            'total_cost': round(total_cost),
            'itinerary': daily_plans,
            'description': self._generate_description(daily_plans, city_name, days)
        }

        return route

    def _directional_sort(self, weighted_pois):
        """
        方向性排序算法
        
        核心思想：
        1. 计算所有POI的中心点
        2. 确定最优游览方向（选择纬度跨度更大的方向：南北或东西）
        3. 按该方向排序，同时考虑距离以避免大幅跳跃
        """
        if len(weighted_pois) <= 1:
            return weighted_pois

        pois = [item for item in weighted_pois]
        
        # 计算中心点
        lats = [item['attraction'].latitude for item in pois]
        lngs = [item['attraction'].longitude for item in pois]
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)

        # 判断主方向：选择跨度更大的方向作为主排序轴
        lat_range = max(lats) - min(lats)
        lng_range = max(lngs) - min(lngs)

        # 使用贪心最近邻算法，兼顾方向性
        # 思路：从最边缘的点开始，每次选择最近且方向一致的下一个点
        sorted_result = []
        remaining = list(pois)

        # 确定起始点：最北或最西的点
        if lat_range >= lng_range:
            # 南北方向为主，从最北开始
            remaining.sort(key=lambda x: x['attraction'].latitude, reverse=True)
        else:
            # 东西方向为主，从最西开始
            remaining.sort(key=lambda x: x['attraction'].longitude)

        # 贪心最近邻 + 方向性约束
        current = remaining.pop(0)
        sorted_result.append(current)

        while remaining:
            current_lat = current['attraction'].latitude
            current_lng = current['attraction'].longitude

            # 计算每个剩余点到当前点的距离
            # 同时加入方向性惩罚：如果方向不一致，增加虚拟距离
            candidates = []
            for item in remaining:
                a = item['attraction']
                dist = self._haversine_distance(current_lat, current_lng, a.latitude, a.longitude)

                # 方向性惩罚：如果下一个点在主方向的"反方向"，增加惩罚距离
                if lat_range >= lng_range:
                    # 南北向为主，惩罚往北走的点（已从北开始，应该向南）
                    direction_penalty = max(0, (a.latitude - current_lat)) * 50
                else:
                    # 东西向为主，惩罚往西走的点（已从西开始，应该向东）
                    direction_penalty = max(0, (current_lng - a.longitude)) * 50

                # 评分加成：高评分景点优先
                score_bonus = (1 - item['score']) * 20  # 得分低的距离加成更大

                adjusted_dist = dist + direction_penalty + score_bonus
                candidates.append((adjusted_dist, item))

            # 选择调整后距离最短的
            candidates.sort(key=lambda x: x[0])
            best = candidates[0][1]
            remaining.remove(best)
            sorted_result.append(best)
            current = best

        return sorted_result

    def _allocate_daily(self, sorted_pois, days, daily_count, daily_max_time, ticket_budget):
        """将景点分配到每天，考虑时间和预算，确保跨天不重复"""
        daily_plans = []
        used_ids = set()  # 已分配的景点ID，防止重复
        remaining = list(sorted_pois)  # 剩余待分配景点

        for day in range(1, days + 1):
            day_plan = {
                'day': day,
                'attractions': [],
                'total_time': 0,
                'total_ticket': 0
            }

            day_time = 0
            day_ticket = 0
            day_count = 0

            # 从remaining中挑选适合当天时间预算的景点
            i = 0
            while i < len(remaining) and day_count < daily_count:
                item = remaining[i]
                a = item['attraction']

                # 跳过已使用的景点
                if a.id in used_ids:
                    i += 1
                    continue

                # 检查时间预算
                duration = a.suggested_duration or 120
                if day_time + duration > daily_max_time:
                    # 时间超了，先跳过，看后面是否有时间更短的
                    i += 1
                    continue

                # 检查门票预算
                ticket = a.ticket_price or 0
                if day_ticket + ticket > ticket_budget * 1.2:
                    i += 1
                    continue

                # 分配该景点到当天
                day_plan['attractions'].append({
                    'id': a.id,
                    'name': a.name,
                    'latitude': a.latitude,
                    'longitude': a.longitude,
                    'category': a.category,
                    'suggested_duration': duration,
                    'ticket_price': ticket,
                    'address': a.address,
                    'rating': a.rating,
                    'tags': self._safe_json_parse(a.tags, []),
                    'opening_hours': a.opening_hours
                })

                used_ids.add(a.id)
                remaining.pop(i)  # 从剩余列表中移除
                day_time += duration
                day_ticket += ticket
                day_count += 1
                # 注意：pop后i不变，因为后面的元素前移了

            day_plan['total_time'] = day_time
            day_plan['total_ticket'] = day_ticket
            daily_plans.append(day_plan)

        return daily_plans

    def _calculate_center(self, pois):
        """计算POI列表的地理中心"""
        if not pois:
            return 0, 0
        lats = [p['latitude'] for p in pois if p.get('latitude')]
        lngs = [p['longitude'] for p in pois if p.get('longitude')]
        if not lats:
            return 0, 0
        return sum(lats) / len(lats), sum(lngs) / len(lngs)

    def _select_hotel(self, hotels, center_lat, center_lng, budget):
        """根据位置和预算选择酒店"""
        if not hotels:
            return None

        # 计算每个酒店到中心的距离和价格匹配度
        candidates = []
        for h in hotels:
            dist = self._haversine_distance(center_lat, center_lng, h.latitude, h.longitude)
            price = h.price_night or 300

            # 价格匹配度：越接近预算越好
            price_score = 1.0
            if price > budget * 1.5:
                price_score = 0.3  # 超预算太多
            elif price > budget:
                price_score = 0.7  # 略超预算
            elif price < budget * 0.3:
                price_score = 0.5  # 太便宜可能不好
            else:
                price_score = 1.0  # 预算范围内

            # 综合评分：距离近 + 价格合适 + 评分高
            rating = h.rating or 4.0
            total_score = price_score * 0.4 + (1 / (1 + dist)) * 0.3 + (rating / 5.0) * 0.3

            candidates.append((total_score, h))

        # 选评分最高的
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]

        return {
            'id': best.id,
            'name': best.name,
            'latitude': best.latitude,
            'longitude': best.longitude,
            'price_night': best.price_night or 300,
            'price_range': best.price_range,
            'rating': best.rating,
            'address': best.address,
            'star_level': best.star_level
        }

    def _select_restaurants(self, restaurants, day_pois, food_budget):
        """为每天的行程选择餐饮（午餐+晚餐）"""
        if not restaurants or not day_pois:
            return {'lunch': None, 'dinner': None}

        # 取当天行程的中心和最远的两个景点位置
        center_lat, center_lng = self._calculate_center(day_pois)

        # 午餐：靠近上午最后一个景点（假设第2个景点后吃午饭）
        lunch_center = center_lat
        lunch_center_lng = center_lng
        if len(day_pois) >= 2:
            lunch_center = day_pois[1]['latitude']
            lunch_center_lng = day_pois[1]['longitude']
        elif len(day_pois) >= 1:
            lunch_center = day_pois[0]['latitude']
            lunch_center_lng = day_pois[0]['longitude']

        # 晚餐：靠近最后一个景点或酒店
        dinner_center = center_lat
        dinner_center_lng = center_lng
        if day_pois:
            last = day_pois[-1]
            dinner_center = last['latitude']
            dinner_center_lng = last['longitude']

        meal_budget = food_budget / 2  # 午餐和晚餐各一半

        lunch = self._pick_restaurant_near(restaurants, lunch_center, lunch_center_lng, meal_budget)
        dinner = self._pick_restaurant_near(restaurants, dinner_center, dinner_center_lng, meal_budget)

        return {'lunch': lunch, 'dinner': dinner}

    def _pick_restaurant_near(self, restaurants, lat, lng, budget):
        """选择距离指定位置最近的合适餐厅"""
        candidates = []
        for r in restaurants:
            dist = self._haversine_distance(lat, lng, r.latitude, r.longitude)
            price = r.avg_price or 60

            # 价格匹配
            price_score = 1.0
            if price > budget * 1.5:
                price_score = 0.3
            elif price > budget:
                price_score = 0.7

            rating = r.rating or 4.0
            total_score = price_score * 0.3 + (1 / (1 + dist)) * 0.4 + (rating / 5.0) * 0.3

            candidates.append((total_score, r))

        candidates.sort(key=lambda x: x[0], reverse=True)
        if not candidates:
            return None

        best = candidates[0][1]
        return {
            'id': best.id,
            'name': best.name,
            'latitude': best.latitude,
            'longitude': best.longitude,
            'avg_price': best.avg_price or 60,
            'cuisine_type': best.cuisine_type,
            'rating': best.rating,
            'address': best.address
        }

    def _estimate_transport(self, day_pois, transport_mode):
        """估算当日交通时间和费用"""
        if len(day_pois) < 2:
            return {'total_distance': 0, 'total_time': 0, 'cost': 0, 'segments': []}

        segments = []
        total_dist = 0
        total_time = 0

        for i in range(len(day_pois) - 1):
            a = day_pois[i]
            b = day_pois[i + 1]
            dist = self._haversine_distance(a['latitude'], a['longitude'], b['latitude'], b['longitude'])
            total_dist += dist

            # 估算交通时间（简化：自驾30km/h，公交20km/h，含步行时间）
            speed = 30 if transport_mode == 'self-driving' else 20
            time_min = (dist / speed) * 60 + 10  # 加10分钟缓冲

            segments.append({
                'from': a['name'],
                'to': b['name'],
                'distance': round(dist, 1),
                'time': round(time_min),
                'mode': 'driving' if transport_mode == 'self-driving' else 'transit'
            })
            total_time += time_min

        # 估算费用
        if transport_mode == 'self-driving':
            cost = total_dist * 0.8  # 约0.8元/km
        else:
            cost = len(segments) * 8  # 平均每段8元公交/地铁

        return {
            'total_distance': round(total_dist, 1),
            'total_time': round(total_time),
            'cost': round(cost),
            'segments': segments
        }

    def _calculate_day_cost(self, day_plan, transport_mode):
        """计算当天总费用"""
        cost = 0

        # 门票
        for a in day_plan.get('attractions', []):
            cost += a.get('ticket_price', 0)

        # 住宿
        hotel = day_plan.get('hotel')
        if hotel:
            cost += hotel.get('price_night', 300)

        # 餐饮
        meals = day_plan.get('meals', {})
        for meal_type in ['lunch', 'dinner']:
            meal = meals.get(meal_type)
            if meal:
                cost += meal.get('avg_price', 60)

        # 交通
        transport = day_plan.get('transport', {})
        cost += transport.get('cost', 0)

        return round(cost)

    def _generate_description(self, daily_plans, city_name, days):
        """生成路线描述"""
        total_attractions = sum(len(d.get('attractions', [])) for d in daily_plans)
        categories = set()
        for d in daily_plans:
            for a in d.get('attractions', []):
                cat = a.get('category', 'other')
                if cat != 'other':
                    categories.add(cat)

        cat_names = {
            'scenery': '自然风光', 'historical': '历史人文',
            'entertainment': '休闲娱乐', 'religious': '宗教文化',
            'shopping': '购物体验', 'leisure': '休闲放松'
        }

        cat_text = '、'.join([cat_names.get(c, c) for c in categories]) or '综合体验'

        return f"{city_name}{days}日深度游，涵盖{total_attractions}个精选景点，{cat_text}。路线经智能优化，减少路途奔波，让您轻松畅游。"

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """计算两点之间的Haversine距离（公里）"""
        R = 6371  # 地球半径（公里）
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    @staticmethod
    def _safe_json_parse(text, default=None):
        """安全解析JSON字符串"""
        if not text:
            return default or []
        try:
            import json
            return json.loads(text)
        except:
            return default or []