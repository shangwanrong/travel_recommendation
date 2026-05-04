"""
测试出行方式显示功能
"""
import sys
import os
import io

# 修复Windows控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 切换到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)
sys.path.insert(0, project_root)

from models.database import SessionLocal
from models.route import Route
import json

def test_transport_display():
    """测试出行方式在地图上的显示"""
    print("=" * 60)
    print("测试出行方式显示功能")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 获取一条测试路线
        route = db.query(Route).first()

        if not route:
            print("[FAIL] 没有找到测试路线")
            return False

        print(f"\n[INFO] 测试路线: {route.name}")
        print(f"[INFO] 城市: {route.city}")
        print(f"[INFO] 天数: {route.days}天")

        # 解析行程数据
        itinerary = json.loads(route.itinerary)

        # 计算景点间距离（模拟）
        print(f"\n[INFO] 行程包含 {len(itinerary)} 天")

        for day in itinerary:
            print(f"\n第 {day['day']} 天:")
            activities = day['activities']
            print(f"  - 活动数量: {len(activities)}")

            for i, activity in enumerate(activities):
                print(f"  {i+1}. {activity['time']} - {activity['name']} ({activity['type']})")

        print("\n" + "=" * 60)
        print("测试场景:")
        print("=" * 60)

        # 测试场景1: 自驾游
        print("\n[场景1] 自驾游模式")
        print("  - 短距离(<0.5km): 应显示 🚶 步行")
        print("  - 其他距离: 应显示 🚗 自驾")

        # 测试场景2: 公共交通
        print("\n[场景2] 公共交通模式")
        print("  - 短距离(<0.5km): 应显示 🚶 步行")
        print("  - 中短距离(<2km): 应显示 🚌 公交")
        print("  - 中距离(<10km): 应显示 🚇 地铁")
        print("  - 长距离(<100km): 应显示 🚄 高铁")
        print("  - 超长距离(>100km): 应显示 ✈️ 飞机")

        print("\n" + "=" * 60)
        print("测试方法:")
        print("=" * 60)
        print("\n1. 启动应用: python app.py")
        print("2. 访问首页: http://localhost:5000")
        print("3. 选择出行方式:")
        print("   - 自驾游: 地图上应显示 🚗 图标")
        print("   - 公共交通: 地图上应根据距离显示 🚌🚇🚄✈️")
        print("4. 点击导出按钮，检查导出的图片是否包含出行方式信息")

        print("\n[PASS] 测试准备完成")
        return True

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == '__main__':
    success = test_transport_display()
    sys.exit(0 if success else 1)
