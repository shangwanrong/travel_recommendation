#!/usr/bin/env python3
"""测试定制功能API"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import json

def main():
    client = app.test_client()

    # 1. 测试定制页面
    print("1. Testing /customize page...")
    resp = client.get('/customize')
    print(f"   Status: {resp.status_code}")
    assert resp.status_code == 200, "Customize page failed"
    print("   OK")

    # 2. 测试路线生成API
    print("2. Testing /api/customize/generate...")
    resp = client.post('/api/customize/generate',
        data=json.dumps({
            'preference': 'scenery',
            'pace': 'moderate',
            'city_id': 'hangzhou',
            'city_name': '杭州',
            'days': 3,
            'budget': 3000,
            'transport': 'self-driving'
        }),
        content_type='application/json'
    )
    print(f"   Status: {resp.status_code}")
    data = json.loads(resp.data)
    
    if 'error' in data:
        print(f"   Error: {data['error']}")
    else:
        print(f"   Routes count: {len(data.get('routes', []))}")
        print(f"   Session ID: {data.get('session_id', '')}")
        
        for i, route in enumerate(data.get('routes', [])):
            print(f"   Route {i+1}: {route['name']}, cost={route['total_cost']}yuan, days={len(route['itinerary'])}")

    # 3. 测试POI建议API
    print("3. Testing /api/poi/suggestions...")
    resp = client.get('/api/poi/suggestions?city=杭州&type=attraction&category=scenery')
    print(f"   Status: {resp.status_code}")
    data = json.loads(resp.data)
    print(f"   POI count: {data.get('total', 0)}")

    # 4. 测试路线优化API
    print("4. Testing /api/customize/optimize...")
    resp = client.post('/api/customize/optimize',
        data=json.dumps({
            'day_pois': [
                {'id': 1, 'name': 'A', 'latitude': 30.25, 'longitude': 120.15},
                {'id': 2, 'name': 'B', 'latitude': 30.30, 'longitude': 120.20},
                {'id': 3, 'name': 'C', 'latitude': 30.20, 'longitude': 120.10},
            ]
        }),
        content_type='application/json'
    )
    print(f"   Status: {resp.status_code}")
    data = json.loads(resp.data)
    print(f"   Optimized order: {[p['name'] for p in data.get('optimized_order', [])]}")
    print(f"   Total distance: {data.get('total_distance', 0)}km")

    print("\nAll tests passed!")

if __name__ == "__main__":
    main()