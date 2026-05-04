from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from models.database import Base
from datetime import datetime
import json

class CustomRoute(Base):
    """定制路线模型，存储用户生成的定制路线"""
    __tablename__ = 'custom_routes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 关联用户，可为空（未登录用户）
    route_id = Column(String(50), unique=True, nullable=False)  # 路线唯一ID，如 "custom_hz_20260502_001"
    name = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    city_id = Column(String(50))
    days = Column(Integer, nullable=False)
    description = Column(Text)
    total_budget = Column(Float)  # 总预算（元）
    total_duration = Column(Float)  # 总时长（小时）
    
    # 用户偏好数据
    preference_data = Column(Text)  # JSON格式，存储问卷答案
    
    # 路线详细数据
    itinerary = Column(Text)  # JSON格式，存储每日行程
    poi_data = Column(Text)  # JSON格式，存储所有POI的完整数据（用于编辑）
    
    # 交通方式
    transport_mode = Column(String(50))  # 出行方式：public-transport/driving
    
    # 状态标志
    is_finalized = Column(Integer, default=0)  # 是否已确认：0-草稿，1-已确认
    is_shared = Column(Integer, default=0)  # 是否分享：0-私有，1-公开
    
    # 统计信息
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.route_id,
            'name': self.name,
            'city': self.city,
            'city_id': self.city_id,
            'days': self.days,
            'description': self.description,
            'total_budget': self.total_budget,
            'total_duration': self.total_duration,
            'preference_data': json.loads(self.preference_data) if self.preference_data else {},
            'itinerary': json.loads(self.itinerary) if self.itinerary else [],
            'poi_data': json.loads(self.poi_data) if self.poi_data else {},
            'transport_mode': self.transport_mode,
            'is_finalized': self.is_finalized,
            'is_shared': self.is_shared,
            'views': self.views,
            'likes': self.likes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<CustomRoute {self.name} ({self.city}, {self.days}天)>"