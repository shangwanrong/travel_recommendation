from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from models.database import Base
from datetime import datetime
import json

class Attraction(Base):
    __tablename__ = 'attractions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    province = Column(String(50))
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    ticket_price = Column(Float, default=0)
    opening_hours = Column(String(200))
    rating = Column(Float)
    phone = Column(String(50))
    images = Column(Text)  # JSON格式存储图片URL列表
    tags = Column(Text)    # JSON格式存储标签列表
    type_code = Column(String(50))  # POI类型代码
    source = Column(String(50), default='amap')  # 数据来源：amap/baidu/manual
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'province': self.province,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'ticket_price': self.ticket_price,
            'opening_hours': self.opening_hours,
            'rating': self.rating,
            'phone': self.phone,
            'images': json.loads(self.images) if self.images else [],
            'tags': json.loads(self.tags) if self.tags else [],
            'source': self.source
        }

    def __repr__(self):
        return f"<Attraction {self.name} ({self.city})>"
