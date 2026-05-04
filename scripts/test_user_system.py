"""用户系统API测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import json

client = app.test_client()

def test(desc, resp, expected_code=None):
    status = resp.status_code
    try:
        data = resp.get_json()
    except:
        data = None
    mark = "OK" if (expected_code is None or status == expected_code) else "FAIL"
    print(f"  [{mark}] {desc}: {status} {data}")

# 1. 注册
print("=== 注册 ===")
resp = client.post('/api/register', json={'username': 'testuser', 'password': '123456', 'email': 'test@test.com'})
test("正常注册", resp, 201)

resp = client.post('/api/register', json={'username': 'testuser', 'password': '123456'})
test("重复用户名", resp, 409)

resp = client.post('/api/register', json={'username': '', 'password': '123456'})
test("空用户名", resp, 400)

resp = client.post('/api/register', json={'username': 'ab', 'password': '12'})
test("密码太短", resp, 400)

# 2. 用户信息（已注册自动登录）
print("\n=== 用户信息 ===")
resp = client.get('/api/user/info')
data = resp.get_json()
test("获取用户信息", resp, 200)
print(f"  用户名: {data['user']['username']}, 收藏: {data['user'].get('fav_count', 0)}")

# 3. 路线数据
routes_resp = client.get('/api/home')
routes = routes_resp.get_json()
print(f"\n=== 热门路线: {len(routes)} 条 ===")

# 4. 收藏
print("\n=== 收藏 ===")
if routes:
    rid = routes[0]['id']
    resp = client.post('/api/favorite', json={'route_id': rid})
    test("添加收藏", resp, 201)
    
    resp = client.post('/api/favorite', json={'route_id': rid})
    test("重复收藏", resp, 409)
    
    resp = client.get(f'/api/favorite/check/{rid}')
    test("检查收藏状态", resp, 200)
    print(f"  is_favorited: {resp.get_json()['is_favorited']}")
    
    resp = client.get('/api/favorites')
    test("获取收藏列表", resp, 200)
    print(f"  收藏数量: {resp.get_json()['total']}")
    
    resp = client.delete(f'/api/favorite/{rid}')
    test("取消收藏", resp, 200)
    
    resp = client.delete(f'/api/favorite/{rid}')
    test("重复取消", resp, 404)

# 5. 浏览历史
print("\n=== 浏览历史 ===")
if routes:
    rid2 = routes[1]['id'] if len(routes) > 1 else routes[0]['id']
    resp = client.post('/api/history', json={'route_id': rid2})
    test("记录历史", resp, 201)
    
    resp = client.get('/api/history')
    test("获取历史", resp, 200)
    print(f"  历史数量: {resp.get_json()['total']}")
    
    resp = client.delete('/api/history')
    test("清空历史", resp, 200)

# 6. 足迹
print("\n=== 足迹 ===")
resp = client.post('/api/footprint', json={'city': '杭州', 'city_id': 'hangzhou'})
test("添加足迹", resp, 201)

resp = client.post('/api/footprint', json={'city': '杭州', 'city_id': 'hangzhou'})
test("重复足迹", resp, 200)

resp = client.get('/api/footprints')
test("获取足迹", resp, 200)
print(f"  足迹数量: {resp.get_json()['total']}")

# 7. 登出
print("\n=== 登出 ===")
resp = client.post('/api/logout')
test("登出", resp, 200)

# 8. 未登录测试
print("\n=== 未登录测试 ===")
resp = client.post('/api/favorite', json={'route_id': 'test'})
test("未登录收藏", resp, 401)

resp = client.get('/api/favorites')
test("未登录获取收藏", resp, 401)

# 9. 登录
print("\n=== 登录 ===")
resp = client.post('/api/login', json={'username': 'testuser', 'password': '123456'})
test("正确密码登录", resp, 200)

resp = client.post('/api/logout')
resp = client.post('/api/login', json={'username': 'testuser', 'password': 'wrong'})
test("错误密码登录", resp, 401)

# 10. 页面路由
print("\n=== 页面路由 ===")
resp = client.get('/')
test("首页", resp, 200)

resp = client.get('/profile')
test("个人中心", resp, 200)

print("\n=== 全部测试完成 ===")
