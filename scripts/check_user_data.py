#!/usr/bin/env python3
"""
检查用户数据表是否有重要数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.user_data import Favorite, Footprint, BrowseHistory
from models.user import User

def check_user_data():
    db = SessionLocal()
    try:
        # 检查用户数量
        user_count = db.query(User).count()
        print(f"用户表记录数: {user_count}")
        
        # 检查收藏
        favorite_count = db.query(Favorite).count()
        print(f"收藏记录数: {favorite_count}")
        
        # 检查足迹
        footprint_count = db.query(Footprint).count()
        print(f"足迹记录数: {footprint_count}")
        
        # 检查浏览历史
        history_count = db.query(BrowseHistory).count()
        print(f"浏览历史记录数: {history_count}")
        
        # 如果有用户数据，建议导出
        if user_count > 0 or favorite_count > 0 or footprint_count > 0 or history_count > 0:
            print("\n⚠️  警告：数据库中有用户数据！")
            print("建议在重建数据库前导出用户数据。")
            return True
        else:
            print("\n✅ 没有用户数据，可以安全重建数据库。")
            return False
            
    except Exception as e:
        print(f"检查数据时出错: {e}")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    check_user_data()