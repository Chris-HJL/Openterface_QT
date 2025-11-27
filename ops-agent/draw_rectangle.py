#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在图片上绘制矩形框的程序
"""

from PIL import Image, ImageDraw
import sys
import os

def draw_rectangle(image_path, top_left, bottom_right, output_path=None):
    """
    在指定图片上绘制矩形框
    
    参数:
    image_path: 图片路径
    top_left: 左上角坐标 (x, y)
    bottom_right: 右下角坐标 (x, y)
    output_path: 输出图片路径，如果为None则覆盖原图
    """
    
    # 打开图片
    img = Image.open(image_path)
    
    # 创建绘图对象
    draw = ImageDraw.Draw(img)
    
    # 绘制矩形框
    # 注意：Pillow的rectangle函数参数是(左上角坐标, 右下角坐标)
    draw.rectangle([top_left, bottom_right], outline="red", width=2)
    
    # 保存图片
    if output_path is None:
        output_path = image_path
    
    img.save(output_path)
    print(f"矩形框已绘制完成，保存至: {output_path}")

def main():
    # 示例用法
    if len(sys.argv) < 2:
        print("使用方法:")
        print("python draw_rectangle.py <图片路径> <左上角x> <左上角y> <右下角x> <右下角y> [输出路径]")
        print("示例: python draw_rectangle.py image.jpg 100 100 300 200")
        return
    
    # 获取命令行参数
    image_path = sys.argv[1]
    top_left_x = int(sys.argv[2])
    top_left_y = int(sys.argv[3])
    bottom_right_x = int(sys.argv[4])
    bottom_right_y = int(sys.argv[5])
    
    # 如果提供了输出路径
    output_path = None
    if len(sys.argv) >= 7:
        output_path = sys.argv[6]
    
    # 调用绘制函数
    draw_rectangle(image_path, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), output_path)

if __name__ == "__main__":
    main()