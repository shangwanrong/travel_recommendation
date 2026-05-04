"""
全面测试脚本 - 测试所有API端点和功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_api(name, method, url, data=None, expected_status=200):
    """测试API端点"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)

        if response.status_code == expected_status:
            print(f"[PASS] {name}: status {response.status_code}")
            return True, response.json() if response.content else None
        else:
            print(f"[FAIL] {name}: expected {expected_status}, got {response.status_code}")
            return False, None
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False, None

def main():
    print("=" * 60)
    print("智游推荐系统 - 全面功能测试")
    print("=" * 60)

    results = []

    # 1. 测试数据统计API
    print("\n[1] 测试数据统计API")
    success, data = test_api("GET /api/stats", "GET", f"{BASE_URL}/api/stats")
    results.append(success)
    if data:
        print(f"   数据: {json.dumps(data, ensure_ascii=False)}")

    # 2. 测试热门路线API
    print("\n[2] 测试热门路线API")
    success, data = test_api("GET /api/home", "GET", f"{BASE_URL}/api/home")
    results.append(success)
    if data:
        print(f"   返回路线数: {len(data)}")
        if len(data) > 0:
            print(f"   第一条路线: {data[0].get('name', 'N/A')}")

    # 3. 测试城市列表API
    print("\n[3] 测试城市列表API")
    success, data = test_api("GET /api/cities", "GET", f"{BASE_URL}/api/cities")
    results.append(success)
    if data:
        print(f"   省份数: {len(data)}")

    # 4. 测试省份城市API
    print("\n[4] 测试省份城市API")
    success, data = test_api("GET /api/cities?province=浙江省", "GET",
                             f"{BASE_URL}/api/cities?province=浙江省")
    results.append(success)
    if data:
        print(f"   浙江省城市数: {len(data)}")

    # 5. 测试智能推荐API - 杭州3天
    print("\n[5] 测试智能推荐API - 杭州3天")
    success, data = test_api("POST /api/recommend (杭州3天)", "POST",
                             f"{BASE_URL}/api/recommend",
                             {"city": "hangzhou", "days": 3})
    results.append(success)
    if data:
        print(f"   推荐路线数: {len(data)}")
        for route in data:
            print(f"   - {route.get('name', 'N/A')} ({route.get('days', 0)}天)")

    # 6. 测试智能推荐API - 成都2天
    print("\n[6] 测试智能推荐API - 成都2天")
    success, data = test_api("POST /api/recommend (成都2天)", "POST",
                             f"{BASE_URL}/api/recommend",
                             {"city": "chengdu", "days": 2})
    results.append(success)
    if data:
        print(f"   推荐路线数: {len(data)}")

    # 7. 测试路线详情API
    print("\n[7] 测试路线详情API")
    success, data = test_api("GET /api/route/hangzhou-3days-483", "GET",
                             f"{BASE_URL}/api/route/hangzhou-3days-483")
    results.append(success)
    if data:
        print(f"   路线名称: {data.get('name', 'N/A')}")
        print(f"   天数: {data.get('days', 0)}")
        print(f"   价格: {data.get('price_range', 'N/A')}")

    # 8. 测试404错误
    print("\n[8] 测试404错误处理")
    success, _ = test_api("GET /api/route/nonexistent", "GET",
                          f"{BASE_URL}/api/route/nonexistent",
                          expected_status=404)
    results.append(success)

    # 9. 测试无效推荐请求
    print("\n[9] 测试无效推荐请求")
    success, _ = test_api("POST /api/recommend (无city)", "POST",
                          f"{BASE_URL}/api/recommend",
                          {"days": 3},
                          expected_status=400)
    results.append(success)

    # 10. 测试清除缓存API
    print("\n[10] 测试清除缓存API")
    success, data = test_api("POST /api/admin/clear-cache", "POST",
                             f"{BASE_URL}/api/admin/clear-cache")
    results.append(success)
    if data:
        print(f"   响应: {data.get('message', 'N/A')}")

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {passed/total*100:.1f}%")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[WARNING] Some tests failed, please check logs")
        return 1

if __name__ == "__main__":
    exit(main())
