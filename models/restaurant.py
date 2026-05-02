from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from models.database import Base
from datetime import datetime
import json

class Restaurant(Base):
    __tablename__ = 'restaurants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    province = Column(String(50))
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    avg_price = Column(Float)  # 人均消费
    rating = Column(Float)
    phone = Column(String(50))
    images = Column(Text)  # JSON格式
    tags = Column(Text)    # JSON格式，如 ["川菜", "火锅"]
    cuisine_type = Column(String(50))  # 菜系类型
    source = Column(String(50), default='amap')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'province': self.province,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'avg_price': self.avg_price,
            'rating': self.rating,
            'phone': self.phone,
            'images': json.loads(self.images) if self.images else [],
            'tags': json.loads(self.tags) if self.tags else [],
            'cuisine_type': self.cuisine_type,
            'source': self.source
        }

    def __repr__(self):
        return f"<Restaurant {self.name} ({self.city})>"
