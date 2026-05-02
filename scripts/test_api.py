"""
测试高德地图API连接
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.amap_service import AmapService

def main():
    print("\n" + "="*60)
    print("测试高德地图API连接")
    print("="*60)

    try:
        amap = AmapService()
        print(f"\nAPI Key已加载: {amap.api_key[:10]}...")

        # 测试搜索景点
        print("\n测试搜索北京景点...")
        attractions = amap.search_attractions("北京", page=1)

        if attractions:
            print(f"成功获取 {len(attractions)} 个景点")
            print("\n前3个景点：")
            for i, attr in enumerate(attractions[:3], 1):
                print(f"  {i}. {attr['name']}")
                print(f"     地址: {attr['address']}")
                print(f"     坐标: ({attr['latitude']}, {attr['longitude']})")
            print("\nAPI连接测试成功！")
            return True
        else:
            print("未获取到数据")
            return False

    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
