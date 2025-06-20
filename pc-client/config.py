#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

# 应用配置
APP_NAME = "学生拍照系统"
APP_VERSION = "1.0.0"

# 网络配置
DEFAULT_PORT = 8080
CONNECTION_TIMEOUT = 10  # 连接超时时间（秒）
RECEIVE_BUFFER_SIZE = 1024  # 接收缓冲区大小

# 界面配置
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
PHOTO_LIST_WIDTH = 200

# 照片配置
THUMBNAIL_SIZE = 64  # 缩略图大小
DUMMY_PHOTO_SIZE = (800, 600)  # 模拟照片尺寸

# 样式配置
STYLES = {
    'connect_button': """
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
    """,
    'disconnect_button': """
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
    """,
    'photo_button': """
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
    """
}
