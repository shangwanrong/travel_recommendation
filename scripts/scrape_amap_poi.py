"""
高德地图POI数据爬取脚本
从高德地图Web服务API批量获取景点、酒店、餐厅数据
API文档: https://lbs.amap.com/api/webservice/guide/api/search

使用方法:
    python scripts/scrape_amap_poi.py              # 爬取全部城市全部类型
    python scripts/scrape_amap_poi.py --city 杭州   # 只爬取杭州
    python scripts/scrape_amap_poi.py --type attraction  # 只爬取景点
    python scripts/scrape_amap_poi.py --clear       # 清除旧数据后再爬取
"""
import sys
import os
import time
import json
import argparse
import requests
from datetime import datetime

# Windows控制台UTF-8支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from models.database import SessionLocal, Base, engine
from models.attraction import Attraction
from models.hotel import Hotel
from models.restaurant import Restaurant

# 高德地图API Key
AMAP_API_KEY = os.getenv('AMAP_API_KEY', '')

# 15个目标城市及其高德城市编码（adcode）
CITIES = {
    '杭州': '330100',
    '成都': '510100',
    '西安': '610100',
    '厦门': '350200',
    '北京': '110000',
    '丽江': '530700',
    '上海': '310000',
    '三亚': '460200',
    '桂林': '450300',
    '青岛': '370200',
    '苏州': '320500',
    '南京': '320100',
    '重庆': '500000',
    '广州': '440100',
    '深圳': '440300',
}

# POI类型代码（高德分类）
# 参考: https://lbs.amap.com/api/webservice/download
POI_TYPES = {
    'attraction': {
        'keywords': ['风景名胜', '公园广场', '博物馆', '寺庙道观', '纪念馆', '古迹', '景点'],
        'type_codes': ['110100', '110200', '110300', '140100', '140200', '140300'],
        'model': Attraction,
        'name': '景点',
    },
    'hotel': {
        'keywords': ['星级酒店', '商务酒店', '度假酒店', '快捷酒店', '民宿', '酒店'],
        'type_codes': ['100100', '100200', '100300'],
        'model': Hotel,
        'name': '酒店',
    },
    'restaurant': {
        'keywords': ['中餐厅', '外国餐厅', '小吃快餐', '火锅', '特色菜', '餐饮'],
        'type_codes': ['050100', '050200', '050300', '050400', '050500'],
        'model': Restaurant,
        'name': '餐厅',
    }
}

# 每个类型每个城市的最大爬取数量
MAX_COUNT_PER_TYPE = 50


def fetch_poi_page(keywords, city, city_code, type_code=None, page=1, offset=25):
    """
    调用高德POI搜索API获取一页数据
    
    Args:
        keywords: 搜索关键词
        city: 城市名称
        city_code: 城市adcode
        type_code: POI类型代码（可选）
        page: 页码
        offset: 每页条数（最大25）
    
    Returns:
        (pois_list, total_count) 或 (None, 0)
    """
    url = 'https://restapi.amap.com/v3/place/text'
    params = {
        'key': AMAP_API_KEY,
        'keywords': keywords,
        'city': city,
        'citylimit': 'true',
        'offset': offset,
        'page': page,
        'extensions': 'all',  # 返回详细信息
    }
    if type_code:
        params['types'] = type_code
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        if data.get('status') == '1':
            pois = data.get('pois', [])
            total = int(data.get('count', 0))
            return pois, total
        else:
            print(f"  [API Error] {data.get('info', '未知错误')}")
            return None, 0
    except Exception as e:
        print(f"  [Request Error] {str(e)}")
        return None, 0


def parse_poi_to_attraction(poi, city):
    """将高德POI数据解析为景点模型"""
    location = poi.get('location', '').split(',')
    lat = float(location[1]) if len(location) == 2 else None
    lng = float(location[0]) if len(location) == 2 else None
    
    # 解析评分
    rating = None
    try:
        rating = float(poi.get('rating', 0)) if poi.get('rating') else None
    except ValueError:
        pass
    
    # 解析门票价格
    ticket_price = 0
    biz_ext = poi.get('biz_ext', {}) or {}
    if biz_ext.get('cost'):
        try:
            # 可能是 "50元" 或 "50" 或列表
            cost_val = biz_ext['cost']
            if isinstance(cost_val, list):
                cost_val = cost_val[0] if cost_val else '0'
            cost_str = str(cost_val).replace('元', '').strip()
            ticket_price = float(cost_str) if cost_str else 0
        except ValueError:
            pass
    
    # 解析营业时间
    opening_hours = ''
    raw_open_time = biz_ext.get('open_time', '')
    if isinstance(raw_open_time, list):
        opening_hours = '; '.join(str(t) for t in raw_open_time if t)
    elif raw_open_time:
        opening_hours = str(raw_open_time)
    
    # 解析电话（高德API可能返回列表）
    phone = poi.get('tel', '')
    if isinstance(phone, list):
        phone = '; '.join(str(p) for p in phone if p)
    
    # 解析图片
    photos = poi.get('photos', []) or []
    images = [p.get('url', '') for p in photos[:3] if isinstance(p, dict) and p.get('url')]
    
    # 解析标签
    tag_str = poi.get('type', '')
    tags = [t.strip() for t in tag_str.split(';') if t.strip()]
    
    # 解析图片
    photos = poi.get('photos', []) or []
    images = [p.get('url', '') for p in photos[:3] if p.get('url')]
    
    # 解析标签
    tag_str = poi.get('type', '')
    tags = [t.strip() for t in tag_str.split(';') if t.strip()]
    
    return Attraction(
        name=poi.get('name', ''),
        city=city,
        province=poi.get('pname', ''),
        address=poi.get('address', '') or poi.get('pname', '') + poi.get('cityname', '') + poi.get('adname', ''),
        latitude=lat,
        longitude=lng,
        description=poi.get('intro', '') or f"{poi.get('name', '')}位于{city}，是当地知名景点。",
        ticket_price=ticket_price,
        opening_hours=opening_hours,
        rating=rating,
        phone=phone,
        images=json.dumps(images, ensure_ascii=False) if images else '',
        tags=json.dumps(tags[:5], ensure_ascii=False) if tags else '',
        type_code=poi.get('typecode', ''),
        source='amap'
    )


def parse_poi_to_hotel(poi, city):
    """将高德POI数据解析为酒店模型"""
    location = poi.get('location', '').split(',')
    lat = float(location[1]) if len(location) == 2 else None
    lng = float(location[0]) if len(location) == 2 else None
    
    rating = None
    try:
        rating = float(poi.get('rating', 0)) if poi.get('rating') else None
    except ValueError:
        pass
    
    # 解析价格区间
    price_range = ''
    biz_ext = poi.get('biz_ext', {}) or {}
    if biz_ext.get('cost'):
        try:
            cost_val = biz_ext['cost']
            if isinstance(cost_val, list):
                cost_val = cost_val[0] if cost_val else '300'
            cost = float(str(cost_val).replace('元', '').strip())
            price_range = f"{int(cost * 0.8)}-{int(cost * 1.2)}元"
        except ValueError:
            price_range = '200-500元'
    
    # 解析电话
    phone = poi.get('tel', '')
    if isinstance(phone, list):
        phone = '; '.join(str(p) for p in phone if p)
    
    # 解析图片
    photos = poi.get('photos', []) or []
    images = [p.get('url', '') for p in photos[:3] if isinstance(p, dict) and p.get('url')]
    
    tag_str = poi.get('type', '')
    tags = [t.strip() for t in tag_str.split(';') if t.strip()]
    
    # 判断星级
    star_level = ''
    name_lower = poi.get('name', '').lower()
    if '五星级' in tag_str or '豪华' in name_lower:
        star_level = '五星级'
    elif '四星级' in tag_str or '高档' in tag_str:
        star_level = '四星级'
    elif '三星级' in tag_str or '舒适' in tag_str:
        star_level = '三星级'
    elif '快捷' in tag_str or '经济' in tag_str:
        star_level = '经济型'
    else:
        star_level = '商务型'
    
    return Hotel(
        name=poi.get('name', ''),
        city=city,
        province=poi.get('pname', ''),
        address=poi.get('address', '') or poi.get('pname', '') + poi.get('cityname', '') + poi.get('adname', ''),
        latitude=lat,
        longitude=lng,
        description=poi.get('intro', '') or f"{poi.get('name', '')}位于{city}，是当地优质住宿选择。",
        price_range=price_range or '200-500元',
        rating=rating,
        phone=phone,
        images=json.dumps(images, ensure_ascii=False) if images else '',
        tags=json.dumps(tags[:5], ensure_ascii=False) if tags else '',
        star_level=star_level,
        source='amap'
    )


def parse_poi_to_restaurant(poi, city):
    """将高德POI数据解析为餐厅模型"""
    location = poi.get('location', '').split(',')
    lat = float(location[1]) if len(location) == 2 else None
    lng = float(location[0]) if len(location) == 2 else None
    
    rating = None
    try:
        rating = float(poi.get('rating', 0)) if poi.get('rating') else None
    except ValueError:
        pass
    
    # 解析人均消费
    avg_price = None
    biz_ext = poi.get('biz_ext', {}) or {}
    if biz_ext.get('cost'):
        try:
            cost_val = biz_ext['cost']
            if isinstance(cost_val, list):
                cost_val = cost_val[0] if cost_val else '80'
            avg_price = float(str(cost_val).replace('元', '').strip())
        except ValueError:
            pass
    
    # 解析电话
    phone = poi.get('tel', '')
    if isinstance(phone, list):
        phone = '; '.join(str(p) for p in phone if p)
    
    # 解析图片
    photos = poi.get('photos', []) or []
    images = [p.get('url', '') for p in photos[:3] if isinstance(p, dict) and p.get('url')]
    
    tag_str = poi.get('type', '')
    tags = [t.strip() for t in tag_str.split(';') if t.strip()]
    
    # 判断菜系类型
    cuisine_type = '中餐'
    if '川菜' in tag_str or '火锅' in tag_str:
        cuisine_type = '川菜'
    elif '粤菜' in tag_str:
        cuisine_type = '粤菜'
    elif '湘菜' in tag_str:
        cuisine_type = '湘菜'
    elif '鲁菜' in tag_str:
        cuisine_type = '鲁菜'
    elif '江浙菜' in tag_str or '浙菜' in tag_str:
        cuisine_type = '江浙菜'
    elif '日本料理' in tag_str or '日料' in tag_str:
        cuisine_type = '日料'
    elif '韩国料理' in tag_str:
        cuisine_type = '韩餐'
    elif '西餐' in tag_str:
        cuisine_type = '西餐'
    elif '小吃' in tag_str or '快餐' in tag_str:
        cuisine_type = '小吃快餐'
    elif '清真' in tag_str:
        cuisine_type = '清真菜'
    elif '东南亚' in tag_str:
        cuisine_type = '东南亚菜'
    
    return Restaurant(
        name=poi.get('name', ''),
        city=city,
        province=poi.get('pname', ''),
        address=poi.get('address', '') or poi.get('pname', '') + poi.get('cityname', '') + poi.get('adname', ''),
        latitude=lat,
        longitude=lng,
        description=poi.get('intro', '') or f"{poi.get('name', '')}位于{city}，是当地热门餐厅。",
        avg_price=avg_price,
        rating=rating,
        phone=phone,
        images=json.dumps(images, ensure_ascii=False) if images else '',
        tags=json.dumps(tags[:5], ensure_ascii=False) if tags else '',
        cuisine_type=cuisine_type,
        source='amap'
    )


PARSERS = {
    'attraction': parse_poi_to_attraction,
    'hotel': parse_poi_to_hotel,
    'restaurant': parse_poi_to_restaurant,
}


def scrape_city_type(city, city_code, poi_type, max_count=MAX_COUNT_PER_TYPE, session=None):
    """
    爬取指定城市和类型的POI数据
    
    Args:
        city: 城市名称
        city_code: 城市adcode
        poi_type: 'attraction', 'hotel', 'restaurant'
        max_count: 最大爬取数量
        session: 数据库会话
    
    Returns:
        成功插入的数量
    """
    type_config = POI_TYPES[poi_type]
    parser = PARSERS[poi_type]
    model = type_config['model']
    
    all_pois = []
    seen_names = set()
    
    # 使用多个关键词组合搜索，扩大覆盖面
    for keyword in type_config['keywords']:
        for type_code in type_config['type_codes'][:2]:  # 每个关键词只用前2个类型代码
            page = 1
            max_pages = (max_count // 25) + 1
            
            while page <= max_pages and len(all_pois) < max_count:
                pois, total = fetch_poi_page(keyword, city, city_code, type_code, page)
                
                if pois is None:
                    # API错误，等待后重试
                    time.sleep(2)
                    pois, total = fetch_poi_page(keyword, city, city_code, type_code, page)
                    if pois is None:
                        break
                
                for poi in pois:
                    name = poi.get('name', '')
                    if name and name not in seen_names and len(name) > 1:
                        seen_names.add(name)
                        all_pois.append(poi)
                
                if total <= page * 25:
                    break  # 没有更多数据
                
                page += 1
                time.sleep(0.2)  # 控制请求频率
                
                if len(all_pois) >= max_count:
                    break
            
            if len(all_pois) >= max_count:
                break
        if len(all_pois) >= max_count:
            break
    
    # 保存到数据库
    inserted = 0
    for poi in all_pois[:max_count]:
        try:
            # 检查是否已存在（按名称+城市去重）
            existing = session.query(model).filter_by(name=poi.get('name', ''), city=city).first()
            if existing:
                continue
            
            record = parser(poi, city)
            session.add(record)
            inserted += 1
        except Exception as e:
            print(f"  [Save Error] {poi.get('name', '')}: {str(e)}")
    
    session.commit()
    return inserted


def clear_old_data(session, city=None, poi_type=None):
    """清除旧的爬取数据"""
    if poi_type:
        models = [POI_TYPES[poi_type]['model']]
    else:
        models = [Attraction, Hotel, Restaurant]
    
    for model in models:
        query = session.query(model).filter_by(source='amap')
        if city:
            query = query.filter_by(city=city)
        count = query.count()
        query.delete()
        print(f"  清除 {model.__tablename__} 中 {count} 条数据 (city={city or '全部'})")
    
    session.commit()


def main():
    parser = argparse.ArgumentParser(description='高德地图POI数据爬取')
    parser.add_argument('--city', type=str, help='指定城市名称（默认全部）')
    parser.add_argument('--type', type=str, choices=['attraction', 'hotel', 'restaurant'], help='指定POI类型（默认全部）')
    parser.add_argument('--max', type=int, default=MAX_COUNT_PER_TYPE, help=f'每类型每城市最大爬取数量（默认{MAX_COUNT_PER_TYPE}）')
    parser.add_argument('--clear', action='store_true', help='爬取前清除旧数据')
    args = parser.parse_args()
    
    if not AMAP_API_KEY:
        print("❌ 未设置AMAP_API_KEY，请在.env文件中配置")
        return
    
    print("=" * 60)
    print("🗺️  高德地图POI数据爬取工具")
    print("=" * 60)
    
    session = SessionLocal()
    
    try:
        # 清除旧数据
        if args.clear:
            print("\n🗑️  清除旧数据...")
            clear_old_data(session, city=args.city, poi_type=args.type)
        
        # 确定要爬取的城市
        if args.city:
            if args.city in CITIES:
                cities = {args.city: CITIES[args.city]}
            else:
                print(f"❌ 未知城市: {args.city}")
                print(f"支持的城市: {', '.join(CITIES.keys())}")
                return
        else:
            cities = CITIES
        
        # 确定要爬取的类型
        types = [args.type] if args.type else ['attraction', 'hotel', 'restaurant']
        
        total_inserted = 0
        start_time = time.time()
        
        for city, city_code in cities.items():
            print(f"\n{'─' * 40}")
            print(f"📍 城市: {city} (adcode: {city_code})")
            
            for poi_type in types:
                type_name = POI_TYPES[poi_type]['name']
                print(f"\n  🔍 爬取{type_name}...")
                
                try:
                    count = scrape_city_type(city, city_code, poi_type, args.max, session)
                    total_inserted += count
                    print(f"  ✅ {type_name}: 新增 {count} 条")
                except Exception as e:
                    print(f"  ❌ {type_name}爬取失败: {str(e)}")
                    session.rollback()
                
                # 控制请求频率，避免触发限流
                time.sleep(1)
        
        elapsed = time.time() - start_time
        
        # 统计最终数据量
        print(f"\n{'=' * 60}")
        print(f"📊 爬取完成！")
        print(f"   新增数据: {total_inserted} 条")
        print(f"   耗时: {elapsed:.1f}秒")
        
        print(f"\n📈 数据库统计:")
        for model, name in [(Attraction, '景点'), (Hotel, '酒店'), (Restaurant, '餐厅')]:
            total = session.query(model).count()
            amap_count = session.query(model).filter_by(source='amap').count()
            print(f"   {name}: 总计 {total} 条 (高德来源: {amap_count})")
        
        # 按城市统计
        print(f"\n🏙️  各城市景点数量:")
        for city in CITIES:
            count = session.query(Attraction).filter_by(city=city).count()
            bar = '█' * min(count, 30)
            print(f"   {city:4s}: {count:3d} {bar}")
        
    finally:
        session.close()


if __name__ == '__main__':
    main()
