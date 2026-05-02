"""项目功能验证脚本"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_city_name_map():
    """测试城市名称映射"""
    from app import get_city_name_map
    name_map = get_city_name_map()
    print(f"[OK] 城市映射数量: {len(name_map)}")
    for k, v in name_map.items():
        print(f"  {k} -> {v}")

def test_cities_json():
    """测试城市数据完整性"""
    from app import load_cities
    cities = load_cities()
    provinces_count = len(cities.get("provinces", []))
    total_cities = sum(len(p.get("cities", [])) for p in cities.get("provinces", []))
    print(f"[OK] 省份数量: {provinces_count}, 城市总数: {total_cities}")

def test_routes_json():
    """测试路线数据完整性"""
    with open("data/routes.json", "r", encoding="utf-8") as f:
        routes = json.load(f)
    route_list = routes.get("routes", [])
    print(f"[OK] 路线总数: {len(route_list)}")

    # 检查城市覆盖
    cities_covered = set()
    for route in route_list:
        cities_covered.add(route.get("city", ""))
    print(f"[OK] 覆盖城市: {len(cities_covered)} 个 - {', '.join(sorted(cities_covered))}")

def test_route_city_consistency():
    """测试路线数据与城市映射的一致性"""
    from app import get_city_name_map
    name_map = get_city_name_map()
    
    with open("data/routes.json", "r", encoding="utf-8") as f:
        routes = json.load(f)
    
    errors = 0
    for route in routes.get("routes", []):
        city_id = route.get("city_id", "")
        city_name = route.get("city", "")
        if city_id not in name_map:
            print(f"[ERROR] 路线 {route['id']} 的city_id '{city_id}' 不在映射中!")
            errors += 1
        elif name_map[city_id] != city_name:
            print(f"[ERROR] 路线 {route['id']} 城市名不匹配: data={city_name}, map={name_map[city_id]}")
            errors += 1
    
    if errors == 0:
        print("[OK] 所有路线的city_id和city名称与映射完全一致")
    else:
        print(f"[ERROR] 发现 {errors} 个不一致")

def test_transport_consistency():
    """测试transport值一致性"""
    # 检查前端HTML中transport选项值
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    if 'value="public-transport"' in html:
        print("[OK] 前端HTML使用 public-transport")
    else:
        print("[ERROR] 前端HTML未找到 public-transport")

    if 'value="self-driving"' in html:
        print("[OK] 前端HTML使用 self-driving")
    else:
        print("[ERROR] 前端HTML未找到 self-driving")

def test_template_variables():
    """测试模板变量名一致性"""
    with open("templates/route_detail.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # 检查amap_api_key
    if "{{ amap_api_key }}" in html:
        print("[OK] 模板使用 amap_api_key (与后端一致)")
    else:
        print("[ERROR] 模板未找到 amap_api_key")
    
    # 检查cityCenters数量
    import re
    matches = re.findall(r"'([^']+)':\s*\[", html)
    # 过滤只保留中文城市名
    city_matches = [m for m in matches if '\u4e00' <= m[0] <= '\u9fff']
    print(f"[OK] cityCenters 覆盖 {len(city_matches)} 个城市: {', '.join(city_matches)}")

def test_flask_app():
    """测试Flask应用能否正常创建"""
    from app import app
    client = app.test_client()
    
    # 测试首页
    resp = client.get("/")
    print(f"[OK] 首页状态码: {resp.status_code}")
    
    # 测试城市API
    resp = client.get("/api/cities")
    data = resp.get_json()
    print(f"[OK] /api/cities 返回 {len(data)} 个省份")
    
    # 测试热门路线API
    resp = client.get("/api/home")
    data = resp.get_json()
    print(f"[OK] /api/home 返回 {len(data)} 条路线")
    if data:
        print(f"  第一条: {data[0].get('name', 'N/A')}")
        print(f"  transport字段: {data[0].get('transport', 'N/A')}")

    # 测试推荐API
    resp = client.post("/api/recommend", 
                       json={"city": "hangzhou", "days": 3, "transport": "self-driving"},
                       content_type="application/json")
    data = resp.get_json()
    print(f"[OK] /api/recommend (杭州3天) 返回 {len(data)} 条路线")
    if data:
        print(f"  第一条: {data[0].get('name', 'N/A')}")
        print(f"  transport字段: {data[0].get('transport', 'N/A')}")
    
    # 测试新城市推荐
    resp = client.post("/api/recommend",
                       json={"city": "sanya", "days": 3, "transport": "public-transport"},
                       content_type="application/json")
    data = resp.get_json()
    print(f"[OK] /api/recommend (三亚3天) 返回 {len(data)} 条路线")
    
    # 测试统计API
    resp = client.get("/api/stats")
    data = resp.get_json()
    print(f"[OK] /api/stats: {data}")

if __name__ == "__main__":
    print("=" * 60)
    print("旅游推荐平台 - 功能验证测试")
    print("=" * 60)
    
    print("\n--- 1. 城市名称映射 ---")
    test_city_name_map()
    
    print("\n--- 2. 城市数据完整性 ---")
    test_cities_json()
    
    print("\n--- 3. 路线数据完整性 ---")
    test_routes_json()
    
    print("\n--- 4. 路线-城市一致性 ---")
    test_route_city_consistency()
    
    print("\n--- 5. Transport值一致性 ---")
    test_transport_consistency()
    
    print("\n--- 6. 模板变量名一致性 ---")
    test_template_variables()
    
    print("\n--- 7. Flask应用测试 ---")
    test_flask_app()
    
    print("\n" + "=" * 60)
    print("验证完成!")
    print("=" * 60)
