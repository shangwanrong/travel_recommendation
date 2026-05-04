#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试出行方式选择功能
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_recommend_with_transport():
    """测试带出行方式的路线推荐"""
    print("\n=== 测试出行方式推荐功能 ===\n")

    test_cases = [
        {
            "city": "杭州",
            "days": 3,
            "transport": "self-driving",
            "name": "自驾游"
        },
        {
            "city": "杭州",
            "days": 3,
            "transport": "public-transport",
            "name": "公共交通"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"测试 {i}: {case['city']} {case['days']}天 - {case['name']}")

        try:
            response = requests.post(
                f"{BASE_URL}/api/recommend",
                json={
                    "city": case["city"],
                    "days": case["days"],
                    "transport": case["transport"]
                },
                timeout=10
            )

            if response.status_code == 200:
                routes = response.json()
                print(f"  [OK] 返回 {len(routes)} 条路线")

                if routes:
                    route = routes[0]
                    print(f"  路线: {route.get('name', 'N/A')}")
                    print(f"  城市: {route.get('city', 'N/A')}")
                    print(f"  天数: {route.get('days', 'N/A')}")

                    # 测试路线详情页
                    route_id = route.get('id')
                    if route_id:
                        detail_url = f"{BASE_URL}/route/{route_id}?transport={case['transport']}"
                        detail_response = requests.get(detail_url, timeout=10)

                        if detail_response.status_code == 200:
                            html = detail_response.text

                            # 检查是否包含出行方式提示
                            if case['transport'] == 'self-driving':
                                if '自驾游提示' in html:
                                    print(f"  [OK] 详情页包含自驾游提示")
                                else:
                                    print(f"  [FAIL] 详情页缺少自驾游提示")
                            else:
                                if '公共交通提示' in html:
                                    print(f"  [OK] 详情页包含公共交通提示")
                                else:
                                    print(f"  [FAIL] 详情页缺少公共交通提示")
                        else:
                            print(f"  [FAIL] 详情页请求失败: {detail_response.status_code}")
            else:
                print(f"  [FAIL] 请求失败: {response.status_code}")

        except Exception as e:
            print(f"  [FAIL] 异常: {e}")

        print()

def test_route_detail_transport_param():
    """测试路线详情页的transport参数"""
    print("\n=== 测试路线详情页transport参数 ===\n")

    # 获取一条路线
    try:
        response = requests.get(f"{BASE_URL}/api/home", timeout=10)
        if response.status_code == 200:
            routes = response.json()
            if routes:
                route_id = routes[0]['id']

                test_cases = [
                    ("self-driving", "自驾游"),
                    ("public-transport", "公共交通"),
                    (None, "默认")
                ]

                for transport, name in test_cases:
                    if transport:
                        url = f"{BASE_URL}/route/{route_id}?transport={transport}"
                    else:
                        url = f"{BASE_URL}/route/{route_id}"

                    print(f"测试: {name} - {url}")

                    try:
                        detail_response = requests.get(url, timeout=10)
                        if detail_response.status_code == 200:
                            html = detail_response.text

                            if transport == 'self-driving':
                                has_tip = '自驾游提示' in html
                            elif transport == 'public-transport':
                                has_tip = '公共交通提示' in html
                            else:
                                has_tip = '公共交通提示' in html  # 默认应该显示公共交通

                            if has_tip:
                                print(f"  [OK] 正确显示出行方式提示")
                            else:
                                print(f"  [WARN] 未找到出行方式提示")
                        else:
                            print(f"  [FAIL] 请求失败: {detail_response.status_code}")
                    except Exception as e:
                        print(f"  [FAIL] 异常: {e}")

                    print()
    except Exception as e:
        print(f"[FAIL] 获取路线失败: {e}")

def main():
    print("=" * 60)
    print("出行方式功能测试")
    print("=" * 60)

    # 检查服务器是否运行
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"\n[OK] 服务器运行中: {BASE_URL}\n")
    except:
        print(f"\n[FAIL] 服务器未运行，请先启动应用: python app.py\n")
        return

    # 运行测试
    test_recommend_with_transport()
    test_route_detail_transport_param()

    print("=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
