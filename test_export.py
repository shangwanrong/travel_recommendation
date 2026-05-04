"""
测试导出功能
"""
import json
from export_itinerary import generate_itinerary_image

# 读取路线数据
with open('data/routes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找到杭州3天2晚路线
route = None
for r in data['routes']:
    if r['id'] == 'hz-3days-001':
        route = r
        break

if not route:
    print("未找到路线数据")
    exit(1)

# 测试三种样式
styles = ['modern_card', 'subway_map', 'infographic']

print("开始测试导出功能...\n")

for style in styles:
    try:
        output_path = generate_itinerary_image(route, style=style)
        print(f"[OK] {style}: {output_path}")
    except Exception as e:
        print(f"[FAIL] {style}: {e}")
        import traceback
        traceback.print_exc()

print("\n测试完成！")
