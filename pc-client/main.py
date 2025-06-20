#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生拍照系统 - 电脑客户端
用于远程控制手机拍照
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("学生拍照系统")
    app.setApplicationVersion("1.0")
    
    # 设置应用图标
    # app.setWindowIcon(QIcon('resources/icon.png'))
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
