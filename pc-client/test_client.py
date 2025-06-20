#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试客户端功能
"""

import sys
import os
import time
import socket
import threading

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_socket_server():
    """测试Socket服务器（模拟手机端）"""
    print("启动测试服务器...")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('localhost', 8080))
        server_socket.listen(1)
        print("测试服务器已启动，监听端口 8080")
        print("请在客户端中连接到 127.0.0.1:8080")
        
        while True:
            try:
                client_socket, address = server_socket.accept()
                print(f"客户端已连接: {address}")
                
                # 处理客户端请求
                def handle_client(sock):
                    try:
                        while True:
                            data = sock.recv(1024)
                            if not data:
                                break
                                
                            message = data.decode('utf-8').strip()
                            print(f"收到命令: {message}")
                            
                            if message == "TAKE_PHOTO":
                                print("模拟拍照...")
                                time.sleep(1)  # 模拟拍照延迟
                                sock.send("PHOTO_TAKEN".encode('utf-8'))
                                print("已发送拍照完成响应")
                            else:
                                print(f"未知命令: {message}")
                                
                    except Exception as e:
                        print(f"处理客户端时出错: {e}")
                    finally:
                        sock.close()
                        print("客户端连接已关闭")
                
                # 在新线程中处理客户端
                client_thread = threading.Thread(target=handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"服务器错误: {e}")
                
    except Exception as e:
        print(f"启动服务器失败: {e}")
    finally:
        server_socket.close()
        print("测试服务器已关闭")

def test_dependencies():
    """测试依赖包"""
    print("检查依赖包...")
    
    try:
        import PyQt5
        print("✓ PyQt5 已安装")
    except ImportError:
        print("✗ PyQt5 未安装")
        return False
        
    try:
        import PIL
        print("✓ Pillow 已安装")
    except ImportError:
        print("✗ Pillow 未安装")
        return False
        
    try:
        import requests
        print("✓ requests 已安装")
    except ImportError:
        print("✗ requests 未安装")
        return False
        
    print("所有依赖包检查完成")
    return True

def main():
    """主函数"""
    print("学生拍照系统 - 测试工具")
    print("=" * 30)
    
    while True:
        print("\n请选择测试选项:")
        print("1. 检查依赖包")
        print("2. 启动测试服务器（模拟手机端）")
        print("3. 退出")
        
        choice = input("\n请输入选项 (1-3): ").strip()
        
        if choice == "1":
            test_dependencies()
        elif choice == "2":
            try:
                test_socket_server()
            except KeyboardInterrupt:
                print("\n测试服务器已停止")
        elif choice == "3":
            print("退出测试工具")
            break
        else:
            print("无效选项，请重新选择")

if __name__ == '__main__':
    main()
