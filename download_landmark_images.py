import requests
import os
import time

def download_image(url, filename, folder='static/images/attractions'):
    """下载图片到指定文件夹"""
    if not os.path.exists(folder):
        os.makedirs(folder)

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"[OK] {filename}")
            return True
        else:
            print(f"[ERROR] {filename} - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] {filename} - {str(e)}")
        return False

# 使用Lorem Picsum的种子功能为每个城市生成独特的图片
# 每个城市使用不同的种子值确保图片不同
images = {
    # 成都 - 大熊猫基地
    'chengdu_panda.jpg': 'https://picsum.photos/seed/chengdu-panda-base/800/600',

    # 西安 - 兵马俑（已有xian.jpg，再下载一个备用）
    'terracotta.jpg': 'https://picsum.photos/seed/terracotta-warriors/800/600',

    # 厦门 - 鼓浪屿
    'gulangyu.jpg': 'https://picsum.photos/seed/gulangyu-island/800/600',

    # 北京 - 故宫（已有beijing.jpg，再下载一个备用）
    'forbidden_city.jpg': 'https://picsum.photos/seed/forbidden-city-beijing/800/600',

    # 丽江 - 古城
    'lijiang_old_town.jpg': 'https://picsum.photos/seed/lijiang-ancient-town/800/600',

    # 苏州 - 园林（已有拙政园，再下载留园）
    'suzhou_garden.jpg': 'https://picsum.photos/seed/suzhou-classical-garden/800/600',
}

print("开始下载城市标志性景点图片...")
success_count = 0
total = len(images)

for filename, url in images.items():
    print(f"\n正在下载: {filename}")
    if download_image(url, filename):
        success_count += 1
    time.sleep(1)  # 避免请求过快

print(f"\n下载完成: {success_count}/{total} 张图片")
