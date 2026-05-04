import requests
import os
from pathlib import Path

# 创建图片目录
Path("static/images/attractions").mkdir(parents=True, exist_ok=True)
Path("static/images/dining").mkdir(parents=True, exist_ok=True)
Path("static/images/hotels").mkdir(parents=True, exist_ok=True)
Path("static/images/transport").mkdir(parents=True, exist_ok=True)

# 景点图片URL映射（使用稳定的图片源）
images = {
    # 杭州景点
    "xihu.jpg": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=800&h=600&fit=crop",  # 西湖
    "leifengta.jpg": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800&h=600&fit=crop",  # 雷峰塔
    "lingyin.jpg": "https://images.unsplash.com/photo-1580837119756-563d608dd119?w=800&h=600&fit=crop",  # 灵隐寺

    # 苏州景点
    "zhuozhengyuan.jpg": "https://images.unsplash.com/photo-1590735213920-68192a487bc2?w=800&h=600&fit=crop",  # 拙政园
    "hushuguan.jpg": "https://images.unsplash.com/photo-1598948485421-33a1655d3c18?w=800&h=600&fit=crop",  # 虎丘
    "pingjiang.jpg": "https://images.unsplash.com/photo-1589397497843-c6e0ea4e0b8e?w=800&h=600&fit=crop",  # 平江路

    # 南京景点
    "zhongshanling.jpg": "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=800&h=600&fit=crop",  # 中山陵
    "fuzimiao.jpg": "https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=800&h=600&fit=crop",  # 夫子庙

    # 上海景点
    "waitan.jpg": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800&h=600&fit=crop",  # 外滩
    "dongfangmingzhu.jpg": "https://images.unsplash.com/photo-1537981634-5d6f2e1f2e5d?w=800&h=600&fit=crop",  # 东方明珠

    # 通用图片
    "restaurant.jpg": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&h=600&fit=crop",  # 餐厅
    "hotel.jpg": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&h=600&fit=crop",  # 酒店
    "train.jpg": "https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=800&h=600&fit=crop",  # 高铁
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
    elif "train" in filename:
        folder = "transport"
    else:
        folder = "attractions"

    if download_image(url, filename, folder):
        success_count += 1

print(f"\n下载完成: {success_count}/{total_count} 张图片成功")
