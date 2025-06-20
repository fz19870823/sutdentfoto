#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口界面
"""

import sys
import socket
import threading
import time
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, 
                             QGroupBox, QGridLayout, QMessageBox, QProgressBar,
                             QListWidget, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor

from core.phone_controller import PhoneController
from ui.photo_viewer import PhotoViewer
import config

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.phone_controller = PhoneController()
        self.photo_viewer = PhotoViewer()
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f"{config.APP_NAME} - 电脑客户端 v{config.APP_VERSION}")
        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧照片查看器
        splitter.addWidget(self.photo_viewer)
        
        # 设置分割器比例
        splitter.setSizes([400, 800])
        
        # 设置状态栏
        self.statusBar().showMessage("就绪")
        
    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 连接设置组
        connection_group = QGroupBox("连接设置")
        connection_layout = QGridLayout(connection_group)
        
        # IP地址输入
        connection_layout.addWidget(QLabel("手机IP地址:"), 0, 0)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("例如: 192.168.1.100")
        connection_layout.addWidget(self.ip_input, 0, 1)
        
        # 端口输入
        connection_layout.addWidget(QLabel("端口:"), 1, 0)
        self.port_input = QLineEdit("8080")
        connection_layout.addWidget(self.port_input, 1, 1)
        
        # 连接按钮
        self.connect_btn = QPushButton("连接手机")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        connection_layout.addWidget(self.connect_btn, 2, 0, 1, 2)
        
        layout.addWidget(connection_group)
        
        # 控制按钮组
        control_group = QGroupBox("拍照控制")
        control_layout = QVBoxLayout(control_group)
        
        # 拍照按钮
        self.photo_btn = QPushButton("📸 拍照")
        self.photo_btn.setEnabled(False)
        self.photo_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.photo_btn)
        

        
        layout.addWidget(control_group)
        
        # 状态信息组
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout(status_group)
        
        # 连接状态
        self.status_label = QLabel("状态: 未连接")
        status_layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_group)
        
        # 日志输出
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # 清除日志按钮
        clear_log_btn = QPushButton("清除日志")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
        
    def setup_connections(self):
        """设置信号连接"""
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.photo_btn.clicked.connect(self.take_photo)
        
        # 连接手机控制器的信号
        self.phone_controller.connected.connect(self.on_connected)
        self.phone_controller.disconnected.connect(self.on_disconnected)
        self.phone_controller.photo_taken.connect(self.on_photo_taken)
        self.phone_controller.error_occurred.connect(self.on_error)
        self.phone_controller.log_message.connect(self.add_log)
        
    def toggle_connection(self):
        """切换连接状态"""
        if self.phone_controller.is_connected():
            self.phone_controller.disconnect()
        else:
            ip = self.ip_input.text().strip()
            port = self.port_input.text().strip()
            
            if not ip:
                QMessageBox.warning(self, "警告", "请输入手机IP地址")
                return
                
            try:
                port = int(port)
            except ValueError:
                QMessageBox.warning(self, "警告", "端口必须是数字")
                return
                
            self.phone_controller.connect_to_phone(ip, port)
            
    def take_photo(self):
        """拍照"""
        self.phone_controller.take_photo()
        

            
    def on_connected(self):
        """连接成功回调"""
        self.status_label.setText("状态: 已连接")
        self.status_label.setStyleSheet("color: green;")
        self.connect_btn.setText("断开连接")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.photo_btn.setEnabled(True)
        self.ip_input.setEnabled(False)
        self.port_input.setEnabled(False)
        
    def on_disconnected(self):
        """断开连接回调"""
        self.status_label.setText("状态: 未连接")
        self.status_label.setStyleSheet("color: red;")
        self.connect_btn.setText("连接手机")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.photo_btn.setEnabled(False)
        self.ip_input.setEnabled(True)
        self.port_input.setEnabled(True)
        
    def on_photo_taken(self, photo_path):
        """拍照成功回调"""
        self.add_log(f"拍照成功: {photo_path}")
        # 在照片查看器中显示照片
        self.photo_viewer.add_photo(photo_path)
        
    def on_error(self, error_msg):
        """错误回调"""
        self.add_log(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", error_msg)
        
    def add_log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
