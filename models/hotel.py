from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from models.database import Base
from datetime import datetime
import json

class Hotel(Base):
    __tablename__ = 'hotels'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    province = Column(String(50))
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    price_range = Column(String(50))  # 价格区间，如 "200-400元"
    rating = Column(Float)
    phone = Column(String(50))
    images = Column(Text)  # JSON格式
    tags = Column(Text)    # JSON格式，如 ["商务酒店", "近地铁"]
    star_level = Column(String(20))  # 星级，如 "四星级"
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
            'price_range': self.price_range,
            'rating': self.rating,
            'phone': self.phone,
            'images': json.loads(self.images) if self.images else [],
            'tags': json.loads(self.tags) if self.tags else [],
            'star_level': self.star_level,
            'source': self.source
        }

    def __repr__(self):
        return f"<Hotel {self.name} ({self.city})>"
