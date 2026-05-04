#!/usr/bin/env python3
"""
数据库迁移脚本
为新增字段填充默认值，更新现有数据
"""
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant
from models.route import Route

def classify_attraction(tags_str):
    """根据tags字段（JSON中文标签）判断景点分类和游玩时间"""
    tags = []
    if tags_str:
        try:
            tags = json.loads(tags_str)
        except:
            pass
    
    # 将tags列表合并为一个字符串方便匹配
    tags_text = '|'.join(tags) if tags else ''
    
    # 分类映射规则（优先级从高到低）
    category = 'other'
    duration = 120  # 默认2小时
    
    # 宗教类
    if any(k in tags_text for k in ['寺庙道观', '回教寺', '教堂']):
        category = 'religious'
        duration = 60  # 1小时
    # 历史文化类
    elif any(k in tags_text for k in ['博物馆', '纪念馆', '红色景区', '世界遗产']):
        category = 'historical'
        duration = 150  # 2.5小时
    # 娱乐类
    elif any(k in tags_text for k in ['影剧院', '剧场', '动物园', '水族馆', '植物园']):
        category = 'entertainment'
        duration = 180  # 3小时
    # 购物类
    elif any(k in tags_text for k in ['购物服务', '特色商业街', '花鸟鱼虫市场', '花卉市场']):
        category = 'shopping'
        duration = 90  # 1.5小时
    # 风景类
    elif any(k in tags_text for k in ['风景名胜', '公园', '公园广场', '海滩', '岛屿', 
                                       '观景点', '国家级景点', '省级景点', '城市广场']):
        category = 'scenery'
        duration = 180  # 3小时
    # 休闲类
    elif any(k in tags_text for k in ['体育休闲', '休闲场所', '采摘园']):
        category = 'leisure'
        duration = 120  # 2小时
    # 其他
    else:
        category = 'other'
        duration = 90  # 1.5小时
    
    return category, duration

def migrate_attractions():
    """迁移景点数据：填充建议游玩时间和分类"""
    db = SessionLocal()
    try:
        attractions = db.query(Attraction).all()
        print(f"开始迁移 {len(attractions)} 个景点数据...")
        
        updated_count = 0
        for attraction in attractions:
            # 使用tags字段进行智能分类
            category, duration = classify_attraction(attraction.tags)
            
            need_update = False
            # 强制更新所有记录的分类和时长（因为之前的迁移逻辑有误）
            if attraction.category != category:
                attraction.category = category
                need_update = True
            if attraction.suggested_duration != duration:
                attraction.suggested_duration = duration
                need_update = True
            
            if need_update:
                updated_count += 1
        
        db.commit()
        print(f"景点数据迁移完成，更新了 {updated_count} 条记录")
        
    except Exception as e:
        db.rollback()
        print(f"景点数据迁移失败: {e}")
        raise
    finally:
        db.close()

def migrate_hotels():
    """迁移酒店数据：从price_range提取price_night"""
    db = SessionLocal()
    try:
        hotels = db.query(Hotel).all()
        print(f"开始迁移 {len(hotels)} 个酒店数据...")
        
        updated_count = 0
        for hotel in hotels:
            if hotel.price_night is None and hotel.price_range:
                try:
                    # 尝试从price_range中提取价格，如 "200-400元"
                    price_str = hotel.price_range.replace('元', '').replace('¥', '').strip()
                    if '-' in price_str:
                        # 取中间值
                        parts = price_str.split('-')
                        if len(parts) == 2:
                            low = float(parts[0].strip())
                            high = float(parts[1].strip())
                            hotel.price_night = (low + high) / 2
                        else:
                            hotel.price_night = 300  # 默认
                    else:
                        # 尝试解析单个价格
                        try:
                            hotel.price_night = float(price_str)
                        except:
                            hotel.price_night = 300  # 默认
                except:
                    hotel.price_night = 300  # 默认值
                updated_count += 1
            elif hotel.price_night is None:
                hotel.price_night = 300  # 默认值
                updated_count += 1
        
        db.commit()
        print(f"酒店数据迁移完成，更新了 {updated_count} 条记录")
        
    except Exception as e:
        db.rollback()
        print(f"酒店数据迁移失败: {e}")
        raise
    finally:
        db.close()

def migrate_routes():
    """迁移路线数据：设置is_custom默认值"""
    db = SessionLocal()
    try:
        routes = db.query(Route).all()
        print(f"开始迁移 {len(routes)} 条路线数据...")
        
        updated_count = 0
        for route in routes:
            if route.is_custom is None:
                route.is_custom = 0  # 默认不是定制路线
                updated_count += 1
            if route.preference_data is None:
                route.preference_data = '{}'  # 空JSON对象
                updated_count += 1
        
        db.commit()
        print(f"路线数据迁移完成，更新了 {updated_count} 条记录")
        
    except Exception as e:
        db.rollback()
        print(f"路线数据迁移失败: {e}")
        raise
    finally:
        db.close()

def main():
    """主迁移函数"""
    print("开始数据库迁移...")
    
    # 按顺序迁移各表
    migrate_attractions()
    migrate_hotels()
    migrate_routes()
    
    print("数据库迁移完成！")

if __name__ == "__main__":
    main()