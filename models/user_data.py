from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from models.database import Base
from datetime import datetime


class Favorite(Base):
    """收藏表 — 用户收藏路线"""
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    route_id = Column(String(50), nullable=False)  # 对应 Route.route_id
    created_at = Column(DateTime, default=datetime.now)

    # 联合唯一约束：同一用户不能重复收藏同一路线
    __table_args__ = (
        UniqueConstraint('user_id', 'route_id', name='uq_user_route_favorite'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'route_id': self.route_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Footprint(Base):
    """旅行足迹表 — 用户去过的景点"""
    __tablename__ = 'footprints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    city = Column(String(50), nullable=False)  # 城市名称
    city_id = Column(String(50))  # 城市ID
    attraction_name = Column(String(200))  # 景点名称
    latitude = Column(String(20))  # 景点纬度
    longitude = Column(String(20))  # 景点经度
    visited_at = Column(DateTime, default=datetime.now)  # 标记去过的时间

    __table_args__ = (
        UniqueConstraint('user_id', 'attraction_name', name='uq_user_attraction_footprint'),
    )

    def to_dict(self):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'city': self.city,
            'city_id': self.city_id or '',
            'attraction_name': self.attraction_name or '',
            'visited_at': self.visited_at.strftime('%Y-%m-%d') if self.visited_at else ''
        }
        if self.latitude and self.longitude:
            result['latitude'] = float(self.latitude)
            result['longitude'] = float(self.longitude)
        return result


class BrowseHistory(Base):
    """浏览历史表 — 用户查看过的路线"""
    __tablename__ = 'browse_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    route_id = Column(String(50), nullable=False)  # 对应 Route.route_id
    viewed_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'route_id': self.route_id,
            'viewed_at': self.viewed_at.strftime('%Y-%m-%d %H:%M') if self.viewed_at else ''
        }
