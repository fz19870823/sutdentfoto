#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试连接和拍照功能
"""

import socket
import time
import sys

def test_connection_and_photo(ip, port=8080):
    """测试连接和拍照功能"""
    print(f"正在连接到 {ip}:{port}...")
    
    try:
        # 创建socket连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))
        
        print("✅ 连接成功!")
        
        # 接收连接确认
        data = sock.recv(1024)
        message = data.decode('utf-8').strip()
        print(f"收到: {message}")
        
        # 发送拍照命令
        print("📸 发送拍照命令...")
        sock.send("TAKE_PHOTO".encode('utf-8'))
        
        # 接收响应
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    break
                    
                message = data.decode('utf-8').strip()
                print(f"收到: {message}")
                
                if message == "COMMAND_RECEIVED":
                    print("✅ 手机已收到拍照命令")
                elif message.startswith("PHOTO_TAKEN"):
                    print("✅ 拍照完成!")
                    if ":" in message:
                        uri = message.split(":", 1)[1]
                        print(f"照片URI: {uri}")
                    break
                    
            except socket.timeout:
                print("等待响应...")
                continue
                
        # 测试心跳
        print("💓 测试心跳...")
        sock.send("PING".encode('utf-8'))
        
        data = sock.recv(1024)
        message = data.decode('utf-8').strip()
        if message == "PONG":
            print("✅ 心跳正常")
        else:
            print(f"心跳响应: {message}")
            
        # 保持连接一段时间
        print("⏰ 保持连接10秒...")
        time.sleep(10)
        
        # 断开连接
        print("🔌 断开连接...")
        sock.send("DISCONNECT".encode('utf-8'))
        sock.close()
        
        print("✅ 测试完成!")
        
    except socket.timeout:
        print("❌ 连接超时")
    except ConnectionRefusedError:
        print("❌ 连接被拒绝，请确保手机应用正在运行")
    except Exception as e:
        print(f"❌ 错误: {e}")

def main():
    """主函数"""
    print("学生拍照系统 - 连接测试")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("请输入手机IP地址 (例如: 10.21.4.170): ").strip()
        
    if not ip:
        print("❌ 请提供有效的IP地址")
        return
        
    test_connection_and_photo(ip)

if __name__ == '__main__':
    main()
