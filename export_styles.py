"""
多种行程图片导出样式
"""
from PIL import Image, ImageDraw, ImageFont
import math

# 类型配置
TYPE_CONFIG = {
    'attraction': {'name': '景点', 'color': '#4A90E2'},
    'dining': {'name': '餐饮', 'color': '#F5A623'},
    'hotel': {'name': '住宿', 'color': '#7B68EE'},
    'transport': {'name': '交通', 'color': '#50C878'}
}

def load_fonts():
    """加载字体"""
    try:
        return {
            'title': ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 52),
            'subtitle': ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 28),
            'day': ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 38),
            'time': ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 24),
            'name': ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 28),
            'desc': ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 20),
            'price': ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 26),
            'small': ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18),
        }
    except:
        default = ImageFont.load_default()
        return {k: default for k in ['title', 'subtitle', 'day', 'time', 'name', 'desc', 'price', 'small']}

def calculate_total_cost(route):
    """计算总费用"""
    total = 0
    for day in route['itinerary']:
        for activity in day['activities']:
            total += activity.get('price', 0)
    return total


# ==================== 样式1: 现代卡片风格 ====================
def style_modern_card(route, output_path):
    """现代卡片风格 - 圆角卡片、阴影、渐变"""
    fonts = load_fonts()

    # 计算尺寸
    width = 1400
    margin = 80
    header_height = 200
    day_spacing = 40
    card_height = 140
    card_spacing = 25

    total_items = sum(len(day['activities']) for day in route['itinerary'])
    height = header_height + len(route['itinerary']) * (100 + day_spacing) + total_items * (card_height + card_spacing) + margin * 2

    # 创建图片
    img = Image.new('RGB', (width, height), '#F8F9FA')
    draw = ImageDraw.Draw(img)

    y = margin

    # 渐变标题背景
    for i in range(header_height):
        ratio = i / header_height
        r = int(137 + (184 - 137) * ratio)
        g = int(196 + (226 - 196) * ratio)
        b = int(244 + (242 - 244) * ratio)
        draw.rectangle([margin, y + i, width - margin, y + i + 1], fill=f'#{r:02x}{g:02x}{b:02x}')

    # 标题
    title_y = y + header_height // 2 - 40
    draw.text((width // 2, title_y), route['name'], fill='white', font=fonts['title'], anchor='mm')

    # 副标题（包含出行方式）
    transport_text = ''
    if route.get('transport') == 'self-driving':
        transport_text = ' | 自驾游'
    elif route.get('transport') == 'public-transport':
        transport_text = ' | 公共交通'

    subtitle = f"{route['description']} | {route['price_range']}{transport_text}"
    draw.text((width // 2, title_y + 50), subtitle, fill='white', font=fonts['subtitle'], anchor='mm')

    # 总费用
    total_cost = calculate_total_cost(route)
    draw.text((width // 2, title_y + 85), f"总费用: ¥{total_cost}", fill='#FFE66D', font=fonts['subtitle'], anchor='mm')

    y += header_height + 60

    # 每天的行程
    for day in route['itinerary']:
        # 日期标签
        day_badge_width = 180
        day_badge_height = 60
        badge_x = margin + 40

        # 日期背景（圆角矩形）
        draw.rounded_rectangle(
            [badge_x, y, badge_x + day_badge_width, y + day_badge_height],
            radius=30, fill='#89C4F4', outline='#4A90E2', width=3
        )
        draw.text((badge_x + day_badge_width // 2, y + day_badge_height // 2),
                 f"第 {day['day']} 天", fill='white', font=fonts['day'], anchor='mm')

        y += day_badge_height + 30

        # 活动卡片
        for activity in day['activities']:
            card_x = margin + 60
            card_width = width - margin * 2 - 60

            # 卡片阴影
            shadow_offset = 8
            draw.rounded_rectangle(
                [card_x + shadow_offset, y + shadow_offset,
                 card_x + card_width + shadow_offset, y + card_height + shadow_offset],
                radius=20, fill='#D0D0D0'
            )

            # 卡片主体
            type_info = TYPE_CONFIG.get(activity.get('type', 'attraction'), TYPE_CONFIG['attraction'])
            draw.rounded_rectangle(
                [card_x, y, card_x + card_width, y + card_height],
                radius=20, fill='white', outline=type_info['color'], width=4
            )

            # 左侧色块
            draw.rounded_rectangle(
                [card_x + 15, y + 15, card_x + 25, y + card_height - 15],
                radius=5, fill=type_info['color']
            )

            # 内容
            content_x = card_x + 50
            draw.text((content_x, y + 25), activity['time'], fill='#7F8C8D', font=fonts['time'], anchor='lt')
            draw.text((content_x + 120, y + 25), f"{type_info['name']}",
                     fill=type_info['color'], font=fonts['time'], anchor='lt')

            draw.text((content_x, y + 60), activity['name'], fill='#2C3E50', font=fonts['name'], anchor='lt')

            desc = activity.get('description', '')[:35] + ('...' if len(activity.get('description', '')) > 35 else '')
            draw.text((content_x, y + 95), desc, fill='#95A5A6', font=fonts['desc'], anchor='lt')

            # 价格
            price = activity.get('price', 0)
            if price > 0:
                price_text = f"¥{price}"
                draw.text((card_x + card_width - 120, y + card_height // 2),
                         price_text, fill='#E74C3C', font=fonts['price'], anchor='mm')

            y += card_height + card_spacing

        y += day_spacing

    img.save(output_path, quality=95)
    return output_path


# ==================== 样式2: 鱼骨图风格 ====================
def style_fishbone(route, output_path):
    """鱼骨图风格 - 中央主线，左右分支"""
    fonts = load_fonts()

    width = 1600
    height = 2400
    margin = 100

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # 标题
    y = margin
    draw.text((width // 2, y), route['name'], fill='#2C3E50', font=fonts['title'], anchor='mt')
    y += 70
    draw.text((width // 2, y), f"总费用: ¥{calculate_total_cost(route)}",
             fill='#E74C3C', font=fonts['subtitle'], anchor='mt')

    y += 100

    # 中央主线
    center_x = width // 2
    spine_start_y = y
    spine_end_y = height - margin

    # 绘制主脊柱（渐变色）
    draw.line([center_x, spine_start_y, center_x, spine_end_y], fill='#89C4F4', width=8)

    # 计算每个活动的位置
    total_activities = sum(len(day['activities']) for day in route['itinerary'])
    activity_spacing = (spine_end_y - spine_start_y - 200) / total_activities

    current_y = spine_start_y + 100
    side = 'left'  # 交替左右

    for day in route['itinerary']:
        # 日期标记（在主线上）
        circle_radius = 40
        draw.ellipse([center_x - circle_radius, current_y - circle_radius,
                     center_x + circle_radius, current_y + circle_radius],
                    fill='#4A90E2', outline='#2C3E50', width=4)
        draw.text((center_x, current_y), f"Day\n{day['day']}",
                 fill='white', font=fonts['small'], anchor='mm')

        current_y += 80

        for activity in day['activities']:
            type_info = TYPE_CONFIG.get(activity.get('type', 'attraction'), TYPE_CONFIG['attraction'])

            # 分支线
            branch_length = 250
            if side == 'left':
                branch_x = center_x - branch_length
                draw.line([center_x, current_y, branch_x, current_y], fill=type_info['color'], width=4)

                # 活动卡片
                card_width = 350
                card_height = 100
                card_x = branch_x - card_width - 20

                draw.rounded_rectangle([card_x, current_y - card_height // 2,
                                       card_x + card_width, current_y + card_height // 2],
                                      radius=15, fill='#F8F9FA', outline=type_info['color'], width=3)

                # 内容（右对齐）
                text_x = card_x + card_width - 20
                draw.text((text_x, current_y - 30), f"{activity['name']}",
                         fill='#2C3E50', font=fonts['name'], anchor='rt')
                draw.text((text_x, current_y), activity['time'],
                         fill='#7F8C8D', font=fonts['small'], anchor='rt')
                draw.text((text_x, current_y + 25), f"¥{activity.get('price', 0)}",
                         fill='#E74C3C', font=fonts['desc'], anchor='rt')

                side = 'right'
            else:
                branch_x = center_x + branch_length
                draw.line([center_x, current_y, branch_x, current_y], fill=type_info['color'], width=4)

                # 活动卡片
                card_width = 350
                card_height = 100
                card_x = branch_x + 20

                draw.rounded_rectangle([card_x, current_y - card_height // 2,
                                       card_x + card_width, current_y + card_height // 2],
                                      radius=15, fill='#F8F9FA', outline=type_info['color'], width=3)

                # 内容（左对齐）
                text_x = card_x + 20
                draw.text((text_x, current_y - 30), f"{activity['name']}",
                         fill='#2C3E50', font=fonts['name'], anchor='lt')
                draw.text((text_x, current_y), activity['time'],
                         fill='#7F8C8D', font=fonts['small'], anchor='lt')
                draw.text((text_x, current_y + 25), f"¥{activity.get('price', 0)}",
                         fill='#E74C3C', font=fonts['desc'], anchor='lt')

                side = 'left'

            # 节点圆点
            node_radius = 12
            draw.ellipse([center_x - node_radius, current_y - node_radius,
                         center_x + node_radius, current_y + node_radius],
                        fill=type_info['color'], outline='white', width=3)

            current_y += activity_spacing

    img.save(output_path, quality=95)
    return output_path


# ==================== 样式3: 地铁线路图风格 ====================
def style_subway_map(route, output_path):
    """地铁线路图风格 - 模仿地铁线路图设计"""
    fonts = load_fonts()

    width = 1800
    height = 2200
    margin = 100

    img = Image.new('RGB', (width, height), '#F5F5F5')
    draw = ImageDraw.Draw(img)

    # 标题区域
    draw.rectangle([0, 0, width, 180], fill='#2C3E50')
    draw.text((width // 2, 60), route['name'], fill='white', font=fonts['title'], anchor='mm')
    draw.text((width // 2, 120), f"总费用: ¥{calculate_total_cost(route)} | {route['days']}天{route['days']-1}晚",
             fill='#FFE66D', font=fonts['subtitle'], anchor='mm')

    y = 250
    line_x = margin + 100

    # 每天用不同颜色的线路
    day_colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6']

    for day_idx, day in enumerate(route['itinerary']):
        day_color = day_colors[day_idx % len(day_colors)]

        # 日期标签
        draw.rounded_rectangle([margin, y, margin + 200, y + 60],
                              radius=30, fill=day_color)
        draw.text((margin + 100, y + 30), f"第 {day['day']} 天",
                 fill='white', font=fonts['day'], anchor='mm')

        y += 90

        # 站点
        for idx, activity in enumerate(day['activities']):
            type_info = TYPE_CONFIG.get(activity.get('type', 'attraction'), TYPE_CONFIG['attraction'])

            # 垂直线路
            if idx < len(day['activities']) - 1:
                draw.line([line_x, y + 40, line_x, y + 180], fill=day_color, width=12)

            # 站点圆圈
            circle_radius = 35
            draw.ellipse([line_x - circle_radius, y - circle_radius,
                         line_x + circle_radius, y + circle_radius],
                        fill='white', outline=day_color, width=8)
            draw.text((line_x, y), type_info['name'][:1], font=fonts['time'], anchor='mm', fill=day_color)

            # 站点信息卡片
            card_x = line_x + 80
            card_width = width - card_x - margin
            card_height = 120

            draw.rounded_rectangle([card_x, y - 60, card_x + card_width, y + 60],
                                  radius=15, fill='white', outline=day_color, width=3)

            # 内容
            content_x = card_x + 25
            draw.text((content_x, y - 35), activity['name'],
                     fill='#2C3E50', font=fonts['name'], anchor='lt')
            draw.text((content_x, y - 5), f"{activity['time']} | {activity.get('description', '')[:25]}",
                     fill='#7F8C8D', font=fonts['desc'], anchor='lt')
            draw.text((content_x, y + 25), f"💰 ¥{activity.get('price', 0)}",
                     fill='#E74C3C', font=fonts['desc'], anchor='lt')

            y += 180

        y += 40

    img.save(output_path, quality=95)
    return output_path


# ==================== 样式4: 信息图表风格 ====================
def style_infographic(route, output_path):
    """信息图表风格 - 数据可视化风格"""
    fonts = load_fonts()

    width = 1400
    height = 2600
    margin = 80

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # 顶部装饰条
    for i in range(5):
        color = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6'][i]
        draw.rectangle([i * width // 5, 0, (i + 1) * width // 5, 20], fill=color)

    y = 60

    # 标题
    draw.text((width // 2, y), route['name'], fill='#2C3E50', font=fonts['title'], anchor='mt')
    y += 80

    # 统计信息卡片
    total_cost = calculate_total_cost(route)
    stats = [
        ('天数', f"{route['days']}天"),
        ('费用', f"¥{total_cost}"),
        ('景点', f"{sum(1 for d in route['itinerary'] for a in d['activities'] if a.get('type')=='attraction')}个"),
        ('餐饮', f"{sum(1 for d in route['itinerary'] for a in d['activities'] if a.get('type')=='dining')}次"),
    ]

    stat_width = (width - margin * 2 - 60) // 4
    stat_x = margin

    for label, value in stats:
        draw.rounded_rectangle([stat_x, y, stat_x + stat_width, y + 120],
                              radius=15, fill='#F8F9FA', outline='#89C4F4', width=3)
        draw.text((stat_x + stat_width // 2, y + 50), label, fill='#7F8C8D', font=fonts['desc'], anchor='mm')
        draw.text((stat_x + stat_width // 2, y + 90), value, fill='#2C3E50', font=fonts['name'], anchor='mm')
        stat_x += stat_width + 20

    y += 180

    # 时间轴
    for day in route['itinerary']:
        # 日期横条
        draw.rectangle([margin, y, width - margin, y + 70], fill='#89C4F4')
        draw.text((margin + 40, y + 35), f"DAY {day['day']}",
                 fill='white', font=fonts['day'], anchor='lm')

        y += 90

        # 活动网格
        for activity in day['activities']:
            type_info = TYPE_CONFIG.get(activity.get('type', 'attraction'), TYPE_CONFIG['attraction'])

            # 活动条
            bar_height = 100
            draw.rounded_rectangle([margin + 40, y, width - margin - 40, y + bar_height],
                                  radius=12, fill='white', outline=type_info['color'], width=4)

            # 左侧图标区
            icon_width = 100
            draw.rectangle([margin + 40, y, margin + 40 + icon_width, y + bar_height],
                          fill=type_info['color'])
            draw.text((margin + 40 + icon_width // 2, y + bar_height // 2),
                     type_info['name'], fill='white', font=fonts['name'], anchor='mm')

            # 内容区
            content_x = margin + 40 + icon_width + 25
            draw.text((content_x, y + 25), activity['name'],
                     fill='#2C3E50', font=fonts['name'], anchor='lt')
            draw.text((content_x, y + 55), f"⏰ {activity['time']}",
                     fill='#7F8C8D', font=fonts['desc'], anchor='lt')

            # 价格标签
            price_x = width - margin - 150
            if activity.get('price', 0) > 0:
                draw.rounded_rectangle([price_x, y + 25, price_x + 100, y + 75],
                                      radius=25, fill='#FFE66D')
                draw.text((price_x + 50, y + 50), f"¥{activity['price']}",
                         fill='#E74C3C', font=fonts['price'], anchor='mm')

            y += bar_height + 20

        y += 30

    img.save(output_path, quality=95)
    return output_path


# ==================== 样式5: 手绘风格 ====================
def style_hand_drawn(route, output_path):
    """手绘风格 - 模拟手绘笔记本"""
    fonts = load_fonts()

    width = 1300
    height = 2400
    margin = 100

    # 米黄色纸张背景
    img = Image.new('RGB', (width, height), '#FFF8DC')
    draw = ImageDraw.Draw(img)

    # 笔记本线条
    for i in range(margin + 200, height - margin, 50):
        draw.line([margin, i, width - margin, i], fill='#E0E0E0', width=1)

    # 左侧装订线
    for i in range(margin, height - margin, 80):
        draw.ellipse([40, i, 60, i + 20], fill='#D0D0D0')

    y = margin + 50

    # 手写标题
    draw.text((width // 2, y), route['name'], fill='#2C3E50', font=fonts['title'], anchor='mt')

    # 下划线（手绘风格）
    y += 70
    draw.line([margin + 100, y, width - margin - 100, y], fill='#89C4F4', width=4)
    draw.line([margin + 100, y + 5, width - margin - 100, y + 5], fill='#89C4F4', width=2)

    y += 50
    draw.text((width // 2, y), f"💰 预算: ¥{calculate_total_cost(route)}",
             fill='#E74C3C', font=fonts['subtitle'], anchor='mt')

    y += 100

    # 每天的行程
    for day in route['itinerary']:
        # 日期标签（便签纸风格）
        draw.rectangle([margin + 20, y - 10, margin + 220, y + 60], fill='#FFE66D')
        draw.rectangle([margin + 20, y - 10, margin + 220, y], fill='#F5D76E')  # 顶部阴影
        draw.text((margin + 120, y + 25), f"第 {day['day']} 天",
                 fill='#2C3E50', font=fonts['day'], anchor='mm')

        y += 90

        # 活动列表
        for idx, activity in enumerate(day['activities'], 1):
            type_info = TYPE_CONFIG.get(activity.get('type', 'attraction'), TYPE_CONFIG['attraction'])

            # 复选框
            checkbox_size = 25
            checkbox_x = margin + 50
            draw.rectangle([checkbox_x, y, checkbox_x + checkbox_size, y + checkbox_size],
                          outline='#2C3E50', width=3)
            draw.line([checkbox_x + 5, y + 12, checkbox_x + 10, y + 18], fill='#2ECC71', width=3)
            draw.line([checkbox_x + 10, y + 18, checkbox_x + 20, y + 5], fill='#2ECC71', width=3)

            # 内容
            text_x = checkbox_x + 45
            draw.text((text_x, y), f"{type_info['name']} - {activity['name']}",
                     fill='#2C3E50', font=fonts['name'], anchor='lt')
            draw.text((text_x, y + 35), f"⏰ {activity['time']} | {activity.get('description', '')[:30]}",
                     fill='#7F8C8D', font=fonts['desc'], anchor='lt')

            # 价格标签（高亮笔效果）
            if activity.get('price', 0) > 0:
                price_text = f"¥{activity['price']}"
                price_bbox = draw.textbbox((0, 0), price_text, font=fonts['price'])
                price_width = price_bbox[2] - price_bbox[0]
                price_x = width - margin - price_width - 40

                # 高亮背景
                draw.rectangle([price_x - 10, y + 5, price_x + price_width + 10, y + 40],
                              fill='#FFB6C1')
                draw.text((price_x, y + 20), price_text, fill='#E74C3C', font=fonts['price'], anchor='lt')

            y += 90

        y += 40

    img.save(output_path, quality=95)
    return output_path
