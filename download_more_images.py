import requests
import os
from pathlib import Path

# 使用Pixabay的免费图片（无需API密钥，直接访问）
# 或使用Lorem Picsum的特定种子生成稳定图片

images = {
    # 使用Lorem Picsum的种子功能生成稳定的风景图片
    "lingyin.jpg": "https://picsum.photos/seed/lingyin-temple/800/600",
    "zhuozhengyuan.jpg": "https://picsum.photos/seed/humble-garden/800/600",
    "hushuguan.jpg": "https://picsum.photos/seed/tiger-hill/800/600",
    "pingjiang.jpg": "https://picsum.photos/seed/pingjiang-road/800/600",
    "zhongshanling.jpg": "https://picsum.photos/seed/sun-yat-sen/800/600",
    "fuzimiao.jpg": "https://picsum.photos/seed/confucius-temple/800/600",
    "waitan.jpg": "https://picsum.photos/seed/the-bund/800/600",
    "dongfangmingzhu.jpg": "https://picsum.photos/seed/oriental-pearl/800/600",
    "yuhuangtai.jpg": "https://picsum.photos/seed/jade-emperor/800/600",
    "songchengguzhen.jpg": "https://picsum.photos/seed/songcheng/800/600",
    "liuyuan.jpg": "https://picsum.photos/seed/lingering-garden/800/600",
    "shantang.jpg": "https://picsum.photos/seed/shantang-street/800/600",
    "xuanwuhu.jpg": "https://picsum.photos/seed/xuanwu-lake/800/600",
    "jiming.jpg": "https://picsum.photos/seed/jiming-temple/800/600",
    "yuyuan.jpg": "https://picsum.photos/seed/yuyuan-garden/800/600",
    "tianzifang.jpg": "https://picsum.photos/seed/tianzifang/800/600",

    # 通用图片
    "restaurant.jpg": "https://picsum.photos/seed/restaurant/800/600",
    "hotel.jpg": "https://picsum.photos/seed/hotel-room/800/600",
    "train.jpg": "https://picsum.photos/seed/high-speed-train/800/600",
    "taxi.jpg": "https://picsum.photos/seed/taxi-car/800/600",
}

def download_image(url, filename, folder="attractions"):
    try:
        print(f"正在下载: {filename}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            filepath = f"static/images/{folder}/{filename}"
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"[OK] 下载成功: {filename}")
            return True
        else:
            print(f"[FAIL] 下载失败: {filename} (状态码: {response.status_code})")
            return False
    except Exception as e:
        print(f"[ERROR] 下载出错: {filename} - {str(e)}")
        return False

# 下载所有图片
print("开始下载景点图片...\n")
success_count = 0
total_count = len(images)

for filename, url in images.items():
    if "restaurant" in filename:
        folder = "dining"
    elif "hotel" in filename:
        folder = "hotels"
    elif "train" in filename or "taxi" in filename:
        folder = "transport"
    else:
        folder = "attractions"

    if download_image(url, filename, folder):
        success_count += 1

print(f"\n下载完成: {success_count}/{total_count} 张图片成功")
