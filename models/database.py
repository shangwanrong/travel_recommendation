from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from config import Config

# 创建数据库引擎
DATABASE_URL = Config.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def init_db():
    """初始化数据库，创建所有表"""
    from models.attraction import Attraction
    from models.hotel import Hotel
    from models.restaurant import Restaurant
    from models.route import Route

    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成！")

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
