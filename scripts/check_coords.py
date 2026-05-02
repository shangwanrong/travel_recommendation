"""检查数据库中POI坐标数据的覆盖情况"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant
from models.route import Route
import json

def check_coords():
    s = SessionLocal()
    
    # 检查景点坐标
    attrs = s.query(Attraction).all()
    with_coords = sum(1 for a in attrs if a.latitude and a.longitude)
    print(f'景点: 总数={len(attrs)}, 有坐标={with_coords}, 无坐标={len(attrs)-with_coords}')
    
    hotels = s.query(Hotel).all()
    h_with = sum(1 for h in hotels if h.latitude and h.longitude)
    print(f'酒店: 总数={len(hotels)}, 有坐标={h_with}, 无坐标={len(hotels)-h_with}')
    
    rests = s.query(Restaurant).all()
    r_with = sum(1 for r in rests if r.latitude and r.longitude)
    print(f'餐厅: 总数={len(rests)}, 有坐标={r_with}, 无坐标={len(rests)-r_with}')
    
    print()
    print('--- 有坐标的景点样例 ---')
    for a in attrs[:8]:
        if a.latitude:
            print(f'  {a.name}: [{a.latitude}, {a.longitude}] (城市: {a.city})')
    
    print()
    print('--- 无坐标的景点样例 ---')
    count = 0
    for a in attrs:
        if not a.latitude and count < 10:
            print(f'  {a.name} (城市: {a.city})')
            count += 1
    
    # 检查路线行程中的活动名称能否匹配到坐标
    print()
    print('--- 路线行程活动与坐标匹配检查 ---')
    routes = s.query(Route).all()
    poi_coords = {}
    for a in attrs:
        if a.latitude and a.longitude:
            poi_coords[a.name] = [a.latitude, a.longitude]
    for h in hotels:
        if h.latitude and h.longitude:
            poi_coords[h.name] = [h.latitude, h.longitude]
    for r in rests:
        if r.latitude and r.longitude:
            poi_coords[r.name] = [r.latitude, r.longitude]
    
    total_acts = 0
    matched_acts = 0
    unmatched_names = set()
    
    for route in routes[:5]:  # 检查前5条路线
        rd = route.to_dict()
        print(f'\n路线: {rd["name"]} ({rd["city"]})')
        for day in rd.get('itinerary', []):
            for act in day.get('activities', []):
                total_acts += 1
                name = act.get('name', '')
                if name in poi_coords:
                    matched_acts += 1
                else:
                    unmatched_names.add(name)
    
    print(f'\n总计活动: {total_acts}, 匹配: {matched_acts}, 未匹配: {total_acts - matched_acts}')
    print(f'匹配率: {matched_acts/total_acts*100:.1f}%' if total_acts > 0 else '无数据')
    
    if unmatched_names:
        print(f'\n--- 未匹配的活动名称 ({len(unmatched_names)}个) ---')
        for name in sorted(unmatched_names)[:20]:
            print(f'  "{name}"')
    
    s.close()

if __name__ == '__main__':
    check_coords()
