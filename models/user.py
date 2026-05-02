from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from models.database import Base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    avatar = Column(String(500), default='')  # 头像URL
    bio = Column(Text, default='')  # 个人简介
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def set_password(self, password):
        """设置密码（加密存储）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email or '',
            'avatar': self.avatar or '',
            'bio': self.bio or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

    def __repr__(self):
        return f"<User {self.username}>"
