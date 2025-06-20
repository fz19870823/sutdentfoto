#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装脚本
"""

import sys
import subprocess
import os

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("错误: 需要Python 3.7或更高版本")
        print(f"当前版本: Python {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✓ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装依赖包"""
    print("正在安装依赖包...")
    
    try:
        # 升级pip
        print("升级pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # 安装依赖
        print("安装项目依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✓ 依赖包安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装依赖包失败: {e}")
        return False
    except FileNotFoundError:
        print("✗ 未找到requirements.txt文件")
        return False

def verify_installation():
    """验证安装"""
    print("验证安装...")
    
    try:
        import PyQt5
        print("✓ PyQt5 导入成功")
    except ImportError:
        print("✗ PyQt5 导入失败")
        return False
        
    try:
        import PIL
        print("✓ Pillow 导入成功")
    except ImportError:
        print("✗ Pillow 导入失败")
        return False
        
    try:
        import requests
        print("✓ requests 导入成功")
    except ImportError:
        print("✗ requests 导入失败")
        return False
    
    print("✓ 所有依赖包验证通过")
    return True

def create_desktop_shortcut():
    """创建桌面快捷方式（Windows）"""
    if sys.platform != "win32":
        return
        
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "学生拍照系统.lnk")
        target = os.path.join(os.getcwd(), "run.py")
        wDir = os.getcwd()
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()
        
        print("✓ 桌面快捷方式创建成功")
        
    except ImportError:
        print("提示: 如需创建桌面快捷方式，请安装 pywin32 和 winshell")
    except Exception as e:
        print(f"创建桌面快捷方式失败: {e}")

def main():
    """主安装函数"""
    print("学生拍照系统 - 安装程序")
    print("=" * 30)
    
    # 检查Python版本
    if not check_python_version():
        input("按回车键退出...")
        return
    
    # 安装依赖
    if not install_dependencies():
        input("按回车键退出...")
        return
    
    # 验证安装
    if not verify_installation():
        input("按回车键退出...")
        return
    
    # 创建桌面快捷方式
    create_desktop_shortcut()
    
    print("\n" + "=" * 30)
    print("安装完成！")
    print("\n使用方法:")
    print("1. 双击 start.bat 启动程序（Windows）")
    print("2. 或运行: python run.py")
    print("3. 或运行: python main.py")
    
    print("\n测试方法:")
    print("运行: python test_client.py")
    
    input("\n按回车键退出...")

if __name__ == '__main__':
    main()
