import requests
import os
import time

def download_image(url, filename, folder='static/images/attractions'):
    """下载图片到指定文件夹"""
    if not os.path.exists(folder):
        os.makedirs(folder)

    try:
        response = requests.get(url, timeout=30)
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

# 需要下载的城市景点图片
images = {
    'chengdu': ('https://picsum.photos/800/600?random=30', 'chengdu.jpg'),
    'xian': ('https://picsum.photos/800/600?random=31', 'xian.jpg'),
    'xiamen': ('https://picsum.photos/800/600?random=32', 'xiamen.jpg'),
    'beijing': ('https://picsum.photos/800/600?random=33', 'beijing.jpg'),
    'lijiang': ('https://picsum.photos/800/600?random=34', 'lijiang.jpg'),
}

print("开始下载城市封面图片...")
success_count = 0
for city, (url, filename) in images.items():
    if download_image(url, filename):
        success_count += 1
    time.sleep(1)  # 避免请求过快

print(f"\n下载完成: {success_count}/{len(images)} 张图片")
