"""
路线优化器 - 优化已有路线的景点顺序和时间安排
"""
import math
from models.database import SessionLocal
from models.attraction import Attraction


class RouteOptimizer:
    """路线优化器"""

    def optimize_route(self, route_data):
        """
        优化路线中景点的游览顺序
        
        参数:
            route_data: 包含day_pois列表的字典
            {
                'day_pois': [
                    {'id': 1, 'latitude': 30.2, 'longitude': 120.1, 'name': '景点A'},
                    {'id': 2, 'latitude': 30.3, 'longitude': 120.2, 'name': '景点B'},
                    ...
                ]
            }
            
        返回:
            优化后的景点顺序和时间安排
        """
        day_pois = route_data.get('day_pois', [])
        if not day_pois:
            return {'optimized_order': [], 'total_distance': 0}

        # 使用2-opt算法优化TSP
        optimized = self._two_opt_optimize(day_pois)

        # 计算优化后的总距离
        total_dist = 0
        for i in range(len(optimized) - 1):
            dist = self._haversine_distance(
                optimized[i]['latitude'], optimized[i]['longitude'],
                optimized[i + 1]['latitude'], optimized[i + 1]['longitude']
            )
            total_dist += dist

        return {
            'optimized_order': optimized,
            'total_distance': round(total_dist, 1)
        }

    def _two_opt_optimize(self, pois, max_iterations=100):
        """2-opt算法优化TSP路径"""
        if len(pois) <= 2:
            return pois

        route = list(pois)
        improved = True
        iterations = 0

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            for i in range(len(route) - 1):
                for j in range(i + 2, len(route)):
                    # 计算交换前的距离
                    d1 = self._segment_distance(route, i, i + 1) + self._segment_distance(route, j, j - 1 if j > 0 else 0)

                    # 交换i+1到j之间的路径
                    new_route = route[:i + 1] + route[i + 1:j + 1][::-1] + route[j + 1:]

                    # 计算交换后的距离
                    d2 = self._segment_distance(new_route, i, i + 1) + self._segment_distance(new_route, j, j - 1 if j > 0 else 0)

                    if d2 < d1:
                        route = new_route
                        improved = True

        return route

    def _segment_distance(self, route, i, j):
        """计算路径中两点间的距离"""
        if i >= len(route) or j >= len(route):
            return float('inf')
        return self._haversine_distance(
            route[i]['latitude'], route[i]['longitude'],
            route[j]['latitude'], route[j]['longitude']
        )

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Haversine距离计算"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c