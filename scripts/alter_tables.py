#!/usr/bin/env python3
"""
使用SQL ALTER TABLE语句添加新列，保留现有数据
"""
import sys
import os
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def alter_tables():
    """修改表结构，添加新列"""
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    print(f"连接数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 为attractions表添加新列
        print("为attractions表添加新列...")
        cursor.execute("""
            ALTER TABLE attractions 
            ADD COLUMN suggested_duration INTEGER DEFAULT 120
        """)
        print("  添加 suggested_duration 列")
        
        cursor.execute("""
            ALTER TABLE attractions 
            ADD COLUMN category VARCHAR(50)
        """)
        print("  添加 category 列")
        
        # 2. 为hotels表添加新列
        print("为hotels表添加新列...")
        cursor.execute("""
            ALTER TABLE hotels 
            ADD COLUMN price_night FLOAT
        """)
        print("  添加 price_night 列")
        
        # 3. 为routes表添加新列
        print("为routes表添加新列...")
        cursor.execute("""
            ALTER TABLE routes 
            ADD COLUMN is_custom INTEGER DEFAULT 0
        """)
        print("  添加 is_custom 列")
        
        cursor.execute("""
            ALTER TABLE routes 
            ADD COLUMN preference_data TEXT DEFAULT '{}'
        """)
        print("  添加 preference_data 列")
        
        # 4. 创建custom_routes表（如果不存在）
        print("检查custom_routes表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                route_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                city VARCHAR(50) NOT NULL,
                city_id VARCHAR(50),
                days INTEGER NOT NULL,
                description TEXT,
                total_budget FLOAT,
                total_duration FLOAT,
                preference_data TEXT,
                itinerary TEXT,
                poi_data TEXT,
                transport_mode VARCHAR(50),
                is_finalized INTEGER DEFAULT 0,
                is_shared INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        print("  custom_routes表已就绪")
        
        conn.commit()
        print("[SUCCESS] 表结构修改完成！")
        
        # 显示修改后的表结构
        print("\n表结构概览:")
        tables = ['attractions', 'hotels', 'restaurants', 'routes', 'custom_routes']
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n{table} ({len(columns)}列):")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
    except sqlite3.OperationalError as e:
        # 如果列已存在，忽略错误
        if "duplicate column name" in str(e):
            print(f"[WARNING] 列已存在: {e}")
            conn.rollback()
            # 尝试另一种方法：检查列是否存在
            print("尝试检查列状态...")
        else:
            print(f"[ERROR] 修改表结构时出错: {e}")
            raise
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    alter_tables()