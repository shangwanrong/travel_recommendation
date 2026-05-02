"""
初始化数据库脚本
创建所有数据表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db

if __name__ == "__main__":
    print("开始初始化数据库...")
    init_db()
    print("数据库初始化完成！")
