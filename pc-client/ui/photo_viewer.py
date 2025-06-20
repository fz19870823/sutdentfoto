#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片查看器组件
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QScrollArea, QSizePolicy, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon

class PhotoViewer(QWidget):
    """照片查看器类"""
    
    def __init__(self):
        super().__init__()
        self.photos = []  # 存储照片路径列表
        self.current_photo_index = -1
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("照片查看器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        
        # 左侧照片列表
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("照片列表")
        list_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        list_layout.addWidget(list_label)
        
        self.photo_list = QListWidget()
        self.photo_list.setMaximumWidth(200)
        self.photo_list.itemClicked.connect(self.on_photo_selected)
        list_layout.addWidget(self.photo_list)
        
        # 操作按钮
        btn_layout = QVBoxLayout()
        
        self.save_btn = QPushButton("💾 保存照片")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_current_photo)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("🗑️ 删除照片")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_current_photo)
        btn_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("🧹 清空列表")
        self.clear_btn.clicked.connect(self.clear_photos)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        content_layout.addWidget(list_widget)
        
        # 右侧照片显示区域
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)
        display_layout.setContentsMargins(0, 0, 0, 0)
        
        display_label = QLabel("照片预览")
        display_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        display_layout.addWidget(display_label)
        
        # 滚动区域用于显示大图
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                background-color: #f8f8f8;
                border: 2px dashed #cccccc;
                border-radius: 10px;
                min-height: 400px;
            }
        """)
        self.photo_label.setText("暂无照片\n\n点击左侧列表中的照片进行查看")
        
        self.scroll_area.setWidget(self.photo_label)
        display_layout.addWidget(self.scroll_area)
        
        # 照片信息
        self.info_label = QLabel("照片信息: 无")
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #e8f4f8;
                padding: 8px;
                border-radius: 4px;
                margin-top: 5px;
            }
        """)
        display_layout.addWidget(self.info_label)
        
        content_layout.addWidget(display_widget)
        
        # 设置比例
        content_layout.setStretch(0, 1)  # 左侧列表
        content_layout.setStretch(1, 3)  # 右侧显示区域
        
        layout.addLayout(content_layout)

    def add_photo(self, photo_path):
        """添加照片到列表"""
        if photo_path and os.path.exists(photo_path):
            self.photos.append(photo_path)
            
            # 创建列表项
            item = QListWidgetItem()
            filename = os.path.basename(photo_path)
            item.setText(filename)
            item.setData(Qt.UserRole, photo_path)
            
            # 创建缩略图
            try:
                pixmap = QPixmap(photo_path)
                if not pixmap.isNull():
                    # 创建缩略图
                    thumbnail = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(thumbnail))
            except Exception as e:
                print(f"创建缩略图失败: {e}")
            
            self.photo_list.addItem(item)
            
            # 自动选择新添加的照片
            self.photo_list.setCurrentItem(item)
            self.on_photo_selected(item)
            
    def on_photo_selected(self, item):
        """照片被选中时的处理"""
        if item:
            photo_path = item.data(Qt.UserRole)
            self.current_photo_index = self.photo_list.row(item)
            self.display_photo(photo_path)
            self.save_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
    def display_photo(self, photo_path):
        """显示照片"""
        try:
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                # 缩放照片以适应显示区域
                scaled_pixmap = pixmap.scaled(
                    self.scroll_area.size() * 0.9,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.photo_label.setPixmap(scaled_pixmap)
                self.photo_label.setStyleSheet("")
                
                # 更新照片信息
                file_size = os.path.getsize(photo_path)
                file_size_mb = file_size / (1024 * 1024)
                info_text = f"文件: {os.path.basename(photo_path)} | "
                info_text += f"尺寸: {pixmap.width()}x{pixmap.height()} | "
                info_text += f"大小: {file_size_mb:.2f} MB"
                self.info_label.setText(info_text)
            else:
                self.photo_label.setText("无法加载照片")
                self.info_label.setText("照片信息: 加载失败")
        except Exception as e:
            self.photo_label.setText(f"加载照片时出错:\n{str(e)}")
            self.info_label.setText("照片信息: 加载失败")
            
    def save_current_photo(self):
        """保存当前照片"""
        if self.current_photo_index >= 0:
            current_item = self.photo_list.currentItem()
            if current_item:
                source_path = current_item.data(Qt.UserRole)
                filename = os.path.basename(source_path)
                
                # 打开文件保存对话框
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "保存照片",
                    filename,
                    "图片文件 (*.jpg *.jpeg *.png *.bmp)"
                )
                
                if save_path:
                    try:
                        # 复制文件
                        import shutil
                        shutil.copy2(source_path, save_path)
                        QMessageBox.information(self, "成功", f"照片已保存到:\n{save_path}")
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"保存照片失败:\n{str(e)}")
                        
    def delete_current_photo(self):
        """删除当前照片"""
        if self.current_photo_index >= 0:
            current_item = self.photo_list.currentItem()
            if current_item:
                reply = QMessageBox.question(
                    self,
                    "确认删除",
                    "确定要从列表中删除这张照片吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 从列表中移除
                    row = self.photo_list.row(current_item)
                    self.photo_list.takeItem(row)
                    self.photos.pop(row)
                    
                    # 清空显示
                    if self.photo_list.count() == 0:
                        self.photo_label.clear()
                        self.photo_label.setText("暂无照片\n\n点击左侧列表中的照片进行查看")
                        self.photo_label.setStyleSheet("""
                            QLabel {
                                background-color: #f8f8f8;
                                border: 2px dashed #cccccc;
                                border-radius: 10px;
                                min-height: 400px;
                            }
                        """)
                        self.info_label.setText("照片信息: 无")
                        self.save_btn.setEnabled(False)
                        self.delete_btn.setEnabled(False)
                        self.current_photo_index = -1
                    else:
                        # 选择下一张照片
                        if row < self.photo_list.count():
                            self.photo_list.setCurrentRow(row)
                        else:
                            self.photo_list.setCurrentRow(row - 1)
                        self.on_photo_selected(self.photo_list.currentItem())
                        
    def clear_photos(self):
        """清空照片列表"""
        if self.photo_list.count() > 0:
            reply = QMessageBox.question(
                self,
                "确认清空",
                "确定要清空所有照片吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.photo_list.clear()
                self.photos.clear()
                self.photo_label.clear()
                self.photo_label.setText("暂无照片\n\n点击左侧列表中的照片进行查看")
                self.photo_label.setStyleSheet("""
                    QLabel {
                        background-color: #f8f8f8;
                        border: 2px dashed #cccccc;
                        border-radius: 10px;
                        min-height: 400px;
                    }
                """)
                self.info_label.setText("照片信息: 无")
                self.save_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.current_photo_index = -1
