#!/usr/bin/env python3
"""测试路线生成算法"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.route_generator import RouteGenerator

def main():
    gen = RouteGenerator()
    
    # 测试杭州3日游
    print("=" * 50)
    print("Test: Hangzhou 3-day scenery trip")
    print("=" * 50)
    
    routes = gen.generate_routes(
        preference='scenery',
        pace='moderate',
        city_id='hangzhou',
        city_name='杭州',
        days=3,
        budget=3000,
        transport='self-driving'
    )
    
    print(f"Generated {len(routes)} routes\n")
    
    for i, route in enumerate(routes):
        print(f"--- Route {i+1}: {route['name']} ---")
        print(f"  Total cost: {route['total_cost']} yuan")
        print(f"  Description: {route['description']}")
        
        for day_plan in route['itinerary']:
            day = day_plan['day']
            attractions = day_plan.get('attractions', [])
            hotel = day_plan.get('hotel')
            meals = day_plan.get('meals', {})
            transport = day_plan.get('transport', {})
            
            print(f"\n  Day {day}:")
            for a in attractions:
                print(f"    - {a['name']} ({a['category']}, {a['suggested_duration']}min, ticket={a['ticket_price']}yuan)")
            
            if hotel:
                print(f"    Hotel: {hotel['name']} ({hotel['price_night']}yuan/night)")
            
            if meals.get('lunch'):
                print(f"    Lunch: {meals['lunch']['name']} ({meals['lunch']['avg_price']}yuan)")
            if meals.get('dinner'):
                print(f"    Dinner: {meals['dinner']['name']} ({meals['dinner']['avg_price']}yuan)")
            
            if transport:
                print(f"    Transport: {transport['total_distance']}km, {transport['total_time']}min, {transport['cost']}yuan")
            
            print(f"    Day cost: {day_plan.get('estimated_cost', 0)}yuan")
        
        print()
    
    gen.db.close()

if __name__ == "__main__":
    main()