from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from models.database import Base
from datetime import datetime
import json

class Route(Base):
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String(50), unique=True, nullable=False)  # 如 "hz-3days-001"
    name = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    city_id = Column(String(50))
    province = Column(String(50))
    days = Column(Integer, nullable=False)
    description = Column(Text)
    price_range = Column(String(50))  # 如 "1500-2500元"
    cover_image = Column(String(500))
    rating = Column(Float, default=4.5)
    popularity = Column(Integer, default=0)  # 热度值
    tags = Column(Text)  # JSON格式，如 ["文化古迹", "美食之旅"]
    itinerary = Column(Text)  # JSON格式，存储详细行程
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.route_id,
            'name': self.name,
            'city': self.city,
            'city_id': self.city_id,
            'province': self.province,
            'days': self.days,
            'description': self.description,
            'price_range': self.price_range,
            'cover_image': self.cover_image,
            'rating': self.rating,
            'popularity': self.popularity,
            'tags': json.loads(self.tags) if self.tags else [],
            'itinerary': json.loads(self.itinerary) if self.itinerary else []
        }

    def __repr__(self):
        return f"<Route {self.name} ({self.city}, {self.days}天)>"
