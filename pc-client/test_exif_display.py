#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PC端EXIF方向显示
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QTransform
from PIL import Image

class ExifTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXIF方向测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 查找测试照片
        photo_files = []
        for file in os.listdir('.'):
            if file.startswith('analyze_photo_') and file.endswith('.jpg'):
                photo_files.append(file)
        
        photo_files.sort()
        
        for photo_file in photo_files:
            self.add_photo_comparison(layout, photo_file)
    
    def add_photo_comparison(self, layout, photo_path):
        """添加照片对比显示"""
        # 标题
        title_label = QLabel(f"照片: {photo_path}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(title_label)
        
        # 获取EXIF信息
        try:
            with Image.open(photo_path) as img:
                exif = img.getexif()
                orientation = exif.get(274, 1) if exif else 1
                
            info_label = QLabel(f"EXIF方向: {orientation} - {self.get_orientation_desc(orientation)}")
            info_label.setStyleSheet("color: blue; margin-left: 20px;")
            layout.addWidget(info_label)
        except Exception as e:
            info_label = QLabel(f"EXIF读取失败: {e}")
            info_label.setStyleSheet("color: red; margin-left: 20px;")
            layout.addWidget(info_label)
        
        # 原始显示
        original_label = QLabel("原始显示 (忽略EXIF):")
        original_label.setStyleSheet("margin-left: 20px; margin-top: 10px;")
        layout.addWidget(original_label)
        
        original_pixmap = QPixmap(photo_path)
        if not original_pixmap.isNull():
            scaled_original = original_pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            original_display = QLabel()
            original_display.setPixmap(scaled_original)
            original_display.setStyleSheet("border: 1px solid gray; margin-left: 40px;")
            layout.addWidget(original_display)
        
        # EXIF处理后显示
        exif_label = QLabel("EXIF处理后显示:")
        exif_label.setStyleSheet("margin-left: 20px; margin-top: 10px;")
        layout.addWidget(exif_label)
        
        exif_pixmap = self.load_pixmap_with_exif_orientation(photo_path)
        if not exif_pixmap.isNull():
            scaled_exif = exif_pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            exif_display = QLabel()
            exif_display.setPixmap(scaled_exif)
            exif_display.setStyleSheet("border: 1px solid green; margin-left: 40px; margin-bottom: 20px;")
            layout.addWidget(exif_display)
    
    def get_orientation_desc(self, orientation):
        """获取方向描述"""
        descriptions = {
            1: "正常 (0°)",
            2: "水平翻转",
            3: "旋转180°",
            4: "垂直翻转",
            5: "水平翻转 + 逆时针90°",
            6: "顺时针90°",
            7: "水平翻转 + 顺时针90°",
            8: "逆时针90°"
        }
        return descriptions.get(orientation, "未知")
    
    def load_pixmap_with_exif_orientation(self, photo_path):
        """加载图片并应用EXIF方向信息"""
        try:
            # 使用PIL读取EXIF信息
            with Image.open(photo_path) as img:
                # 获取EXIF方向信息
                exif = img.getexif()
                orientation = exif.get(274, 1) if exif else 1  # 274是Orientation标签
                
                # 加载QPixmap
                pixmap = QPixmap(photo_path)
                if pixmap.isNull():
                    return pixmap
                
                # 根据EXIF方向旋转图片
                if orientation != 1:
                    transform = QTransform()
                    
                    if orientation == 2:
                        # 水平翻转
                        transform.scale(-1, 1)
                    elif orientation == 3:
                        # 旋转180度
                        transform.rotate(180)
                    elif orientation == 4:
                        # 垂直翻转
                        transform.scale(1, -1)
                    elif orientation == 5:
                        # 水平翻转 + 逆时针90度
                        transform.scale(-1, 1)
                        transform.rotate(-90)
                    elif orientation == 6:
                        # 顺时针90度
                        transform.rotate(90)
                    elif orientation == 7:
                        # 水平翻转 + 顺时针90度
                        transform.scale(-1, 1)
                        transform.rotate(90)
                    elif orientation == 8:
                        # 逆时针90度
                        transform.rotate(-90)
                    
                    pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                    print(f"应用EXIF方向 {orientation} 到图片: {photo_path}")
                else:
                    print(f"图片无需旋转 (EXIF方向: {orientation}): {photo_path}")
                
                return pixmap
                
        except Exception as e:
            print(f"处理EXIF方向时出错: {e}")
            # 如果处理失败，返回原始图片
            return QPixmap(photo_path)

def main():
    app = QApplication(sys.argv)
    window = ExifTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
