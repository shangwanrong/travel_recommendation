#!/usr/bin/env python3
"""
更新景点游玩时长 - 更细致的分配
根据景点名称关键词和分类，给出更合理的游玩时长
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.attraction import Attraction

# 关键词 → 游玩时长(分钟) 映射
KEYWORD_DURATION = {
    # 大型景区 3-4小时
    '风景区': 180, '景区': 180, '国家公园': 180, '度假区': 180,
    '名胜区': 180, '世界遗产': 240, '古镇': 180, '古城': 180,
    # 中型景点 2小时
    '公园': 120, '园林': 120, '博物馆': 120, '纪念馆': 90,
    '故居': 90, '寺庙': 90, '教堂': 60, '塔': 60,
    '山': 150, '湖': 120, '瀑布': 120, '溶洞': 120,
    '海滩': 150, '岛屿': 180, '湿地': 120, '森林': 150,
    # 小型景点 1-1.5小时
    '广场': 60, '步行街': 90, '街区': 90, '巷': 60,
    '桥': 45, '亭': 30, '楼': 60, '阁': 45,
    '纪念碑': 45, '雕塑': 30, '牌坊': 30,
    # 休闲娱乐
    '乐园': 240, '游乐园': 240, '水上乐园': 240,
    '动物园': 180, '植物园': 150, '海洋馆': 150,
    '温泉': 180, '漂流': 120,
}

CATEGORY_DURATION = {
    'scenery': 120,       # 自然风光默认2小时
    'historical': 90,     # 历史人文默认1.5小时
    'entertainment': 180, # 休闲娱乐默认3小时
    'religious': 60,      # 宗教文化默认1小时
    'shopping': 90,       # 购物默认1.5小时
    'leisure': 90,        # 休闲默认1.5小时
}

def estimate_duration(name, category):
    """根据景点名称关键词和分类估算游玩时长"""
    # 优先按关键词匹配
    best_duration = None
    best_len = 0
    for keyword, duration in KEYWORD_DURATION.items():
        if keyword in name and len(keyword) > best_len:
            best_duration = duration
            best_len = len(keyword)
    
    if best_duration:
        return best_duration
    
    # 回退到分类默认值
    return CATEGORY_DURATION.get(category, 120)

def main():
    db = SessionLocal()
    try:
        attractions = db.query(Attraction).all()
        updated = 0
        
        for a in attractions:
            new_duration = estimate_duration(a.name, a.category)
            old_duration = a.suggested_duration
            
            if old_duration != new_duration:
                a.suggested_duration = new_duration
                updated += 1
        
        db.commit()
        print(f"[OK] 更新了 {updated}/{len(attractions)} 个景点的游玩时长")
        
        # 统计时长分布
        from collections import Counter
        durations = Counter(a.suggested_duration for a in db.query(Attraction).all())
        for dur, count in sorted(durations.items()):
            print(f"  {dur}分钟: {count}个景点")
            
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == '__main__':
    main()
