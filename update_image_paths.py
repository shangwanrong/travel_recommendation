import json

# 读取routes.json
with open('data/routes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 图片映射关系
image_mapping = {
    # 景点
    '西湖景区': '/static/images/attractions/xihu.jpg',
    '西湖': '/static/images/attractions/xihu.jpg',
    '雷峰塔': '/static/images/attractions/leifengta.jpg',
    '灵隐寺': '/static/images/attractions/xihu.jpg',  # 暂用西湖图
    '宋城': '/static/images/attractions/songchengguzhen.jpg',
    '玉皇山': '/static/images/attractions/yuhuangtai.jpg',
    '拙政园': '/static/images/attractions/zhuozhengyuan.jpg',
    '虎丘': '/static/images/attractions/hushuguan.jpg',
    '留园': '/static/images/attractions/liuyuan.jpg',
    '山塘街': '/static/images/attractions/shantang.jpg',
    '中山陵': '/static/images/attractions/zhongshanling.jpg',
    '夫子庙': '/static/images/attractions/fuzimiao.jpg',
    '玄武湖': '/static/images/attractions/xuanwuhu.jpg',
    '外滩': '/static/images/attractions/waitan.jpg',
    '东方明珠': '/static/images/attractions/dongfangmingzhu.jpg',
    '豫园': '/static/images/attractions/yuyuan.jpg',
    '田子坊': '/static/images/attractions/yuyuan.jpg',  # 暂用豫园图

    # 餐饮
    '楼外楼': '/static/images/dining/restaurant.jpg',
    '知味观': '/static/images/dining/restaurant.jpg',
    '灵隐素斋': '/static/images/dining/restaurant.jpg',
    '外婆家': '/static/images/dining/restaurant.jpg',
    '绿茶餐厅': '/static/images/dining/restaurant.jpg',
    '早餐': '/static/images/dining/restaurant.jpg',
    '素斋': '/static/images/dining/restaurant.jpg',
    '陈麻婆豆腐': '/static/images/dining/restaurant.jpg',
    '火锅': '/static/images/dining/restaurant.jpg',
    '羊肉泡馍': '/static/images/dining/restaurant.jpg',
    '海鲜大排档': '/static/images/dining/restaurant.jpg',
    '南翔小笼': '/static/images/dining/restaurant.jpg',

    # 酒店
    '酒店': '/static/images/hotels/hotel.jpg',
    '西湖如家酒店': '/static/images/hotels/hotel.jpg',

    # 交通
    '高铁': '/static/images/transport/train.jpg',
    '出租车': '/static/images/transport/taxi.jpg',
    '打车': '/static/images/transport/taxi.jpg',
}

# 遍历所有路线
for route in data['routes']:
    # 更新封面图
    if 'cover_image' in route and 'dummyimage' in route['cover_image']:
        # 根据城市设置封面
        if route['city'] == '杭州':
            route['cover_image'] = '/static/images/attractions/xihu.jpg'
        elif route['city'] == '苏州':
            route['cover_image'] = '/static/images/attractions/zhuozhengyuan.jpg'
        elif route['city'] == '南京':
            route['cover_image'] = '/static/images/attractions/zhongshanling.jpg'
        elif route['city'] == '上海':
            route['cover_image'] = '/static/images/attractions/waitan.jpg'

    # 更新行程中的图片
    for day in route.get('itinerary', []):
        for activity in day.get('activities', []):
            if 'image' in activity and 'dummyimage' in activity['image']:
                # 根据活动名称匹配图片
                matched = False
                for keyword, path in image_mapping.items():
                    if keyword in activity['name']:
                        activity['image'] = path
                        matched = True
                        break

                # 如果没有匹配到，根据类型设置默认图片
                if not matched:
                    if activity.get('type') == 'attraction':
                        activity['image'] = '/static/images/attractions/xihu.jpg'
                    elif activity.get('type') == 'dining':
                        activity['image'] = '/static/images/dining/restaurant.jpg'
                    elif activity.get('type') == 'hotel':
                        activity['image'] = '/static/images/hotels/hotel.jpg'
                    elif activity.get('type') == 'transport':
                        if '高铁' in activity['name'] or '火车' in activity['name']:
                            activity['image'] = '/static/images/transport/train.jpg'
                        else:
                            activity['image'] = '/static/images/transport/taxi.jpg'

# 保存更新后的数据
with open('data/routes.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("图片路径更新完成！")
print(f"共更新了 {len(data['routes'])} 条路线")
