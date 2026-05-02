import json

# 读取routes.json
with open('data/routes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 城市封面图映射（使用已有图片）
city_covers = {
    '杭州': '/static/images/attractions/xihu.jpg',
    '苏州': '/static/images/attractions/zhuozhengyuan.jpg',
    '南京': '/static/images/attractions/zhongshanling.jpg',
    '上海': '/static/images/attractions/waitan.jpg',
    '成都': '/static/images/attractions/xihu.jpg',  # 暂用西湖
    '西安': '/static/images/attractions/xian.jpg',
    '厦门': '/static/images/attractions/waitan.jpg',  # 暂用外滩
    '北京': '/static/images/attractions/beijing.jpg',
    '丽江': '/static/images/attractions/xihu.jpg',  # 暂用西湖
}

# 更新所有路线的封面图
updated_count = 0
for route in data['routes']:
    city = route.get('city', '')

    # 更新封面图
    if 'cover_image' in route and 'dummyimage' in route['cover_image']:
        if city in city_covers:
            route['cover_image'] = city_covers[city]
            updated_count += 1
            print(f"更新 {city} 封面图: {city_covers[city]}")

# 保存更新后的数据
with open('data/routes.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n封面图更新完成！共更新 {updated_count} 个封面")
