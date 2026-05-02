"""
行程图片导出功能 - 支持多种样式
"""
from export_styles import (
    style_modern_card,
    style_subway_map,
    style_infographic
)

def generate_itinerary_image(route, style='modern_card', output_path=None):
    """
    生成行程图片

    Args:
        route: 路线数据字典
        style: 样式名称 (modern_card, subway_map, infographic)
        output_path: 输出路径，如果为None则自动生成

    Returns:
        生成的图片路径
    """
    if output_path is None:
        output_path = f"static/images/itinerary_{route['id']}_{style}.png"

    # 根据样式选择生成函数
    style_functions = {
        'modern_card': style_modern_card,
        'subway_map': style_subway_map,
        'infographic': style_infographic,
    }

    style_func = style_functions.get(style, style_modern_card)

    # 生成图片
    return style_func(route, output_path)
