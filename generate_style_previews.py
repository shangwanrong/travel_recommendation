"""
生成所有样式的预览图
"""
import json
from export_styles import (
    style_modern_card,
    style_fishbone,
    style_subway_map,
    style_infographic,
    style_hand_drawn
)

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

# 生成所有样式
styles = [
    ('modern_card', style_modern_card, '现代卡片风格'),
    ('fishbone', style_fishbone, '鱼骨图风格'),
    ('subway_map', style_subway_map, '地铁线路图风格'),
    ('infographic', style_infographic, '信息图表风格'),
    ('hand_drawn', style_hand_drawn, '手绘笔记本风格'),
]

print("开始生成样式预览图...\n")

for style_id, style_func, style_name in styles:
    output_path = f'static/images/preview_{style_id}.png'
    try:
        style_func(route, output_path)
        print(f"[OK] {style_name}: {output_path}")
    except Exception as e:
        print(f"[FAIL] {style_name}: 生成失败 - {e}")

print("\n所有样式预览图生成完成！")
print("\n样式说明:")
print("1. 现代卡片风格 - 圆角卡片、阴影效果、渐变色标题，视觉层次分明，适合社交媒体分享")
print("2. 鱼骨图风格 - 中央主线，左右分支，创意十足，适合展示行程逻辑")
print("3. 地铁线路图风格 - 模仿地铁线路图，每天不同颜色，清晰直观")
print("4. 信息图表风格 - 数据可视化设计，顶部统计卡片，专业感强")
print("5. 手绘笔记本风格 - 米黄色纸张，便签纸标签，复选框设计，温馨亲切")
