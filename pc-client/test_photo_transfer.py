#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试照片传输功能
"""

import socket
import time
import sys
import os

def test_photo_transfer(ip, port=8080):
    """测试照片传输功能"""
    print(f"正在连接到 {ip}:{port}...")
    
    try:
        # 创建socket连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)  # 增加超时时间
        sock.connect((ip, port))
        
        print("✅ 连接成功!")
        
        # 接收连接确认
        data = sock.recv(1024)
        message = data.decode('utf-8').strip()
        print(f"收到: {message}")
        
        # 发送拍照命令
        print("📸 发送拍照命令...")
        sock.send("TAKE_PHOTO".encode('utf-8'))
        
        # 处理响应
        photo_uri = None
        photo_data = None
        
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    break
                    
                message = data.decode('utf-8').strip()
                print(f"收到: {message}")
                
                if message == "COMMAND_RECEIVED":
                    print("✅ 手机已收到拍照命令")
                elif message.startswith("PHOTO_TAKEN:"):
                    photo_uri = message.split(":", 1)[1]
                    print(f"✅ 拍照完成! URI: {photo_uri}")
                elif message.startswith("PHOTO_DATA:"):
                    # 照片数据开始
                    size_str = message.split(":", 1)[1]
                    photo_size = int(size_str)
                    print(f"📥 开始接收照片数据: {photo_size} 字节")
                    
                    # 接收照片数据
                    photo_data = receive_photo_data(sock, photo_size)
                    if photo_data:
                        print(f"✅ 照片数据接收完成: {len(photo_data)} 字节")
                        save_photo(photo_data, photo_uri)
                        break
                    else:
                        print("❌ 照片数据接收失败")
                        break
                        
            except socket.timeout:
                print("⏰ 等待响应...")
                continue
            except UnicodeDecodeError:
                # 可能是二进制照片数据，跳过解码
                print("📥 接收到二进制数据...")
                continue
                
        sock.close()
        print("✅ 测试完成!")
        
    except socket.timeout:
        print("❌ 连接超时")
    except ConnectionRefusedError:
        print("❌ 连接被拒绝，请确保手机应用正在运行")
    except Exception as e:
        print(f"❌ 错误: {e}")

def receive_photo_data(sock, expected_size):
    """接收照片数据"""
    photo_buffer = bytearray()
    bytes_received = 0
    
    try:
        while bytes_received < expected_size:
            remaining = expected_size - bytes_received
            chunk_size = min(4096, remaining)
            
            chunk = sock.recv(chunk_size)
            if not chunk:
                print("❌ 连接中断，照片数据接收不完整")
                return None
            
            photo_buffer.extend(chunk)
            bytes_received += len(chunk)
            
            # 显示进度
            progress = (bytes_received / expected_size) * 100
            print(f"📥 接收进度: {progress:.1f}% ({bytes_received}/{expected_size})")
        
        # 等待结束标记
        print("⏳ 等待结束标记...")
        end_marker = b"\nPHOTO_END\n"
        marker_buffer = bytearray()
        
        while len(marker_buffer) < len(end_marker):
            byte = sock.recv(1)
            if not byte:
                break
            marker_buffer.extend(byte)
            if marker_buffer.endswith(end_marker):
                print("✅ 收到结束标记")
                break
        
        return bytes(photo_buffer)
        
    except Exception as e:
        print(f"❌ 接收照片数据时出错: {e}")
        return None

def save_photo(photo_data, uri=None):
    """保存照片"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"received_photo_{timestamp}.jpg"
        
        # 创建保存目录
        save_dir = "received_photos"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(photo_data)
        
        print(f"💾 照片已保存: {filepath}")
        print(f"📏 文件大小: {len(photo_data)} 字节")
        
        if uri:
            print(f"📱 原始URI: {uri}")
            
    except Exception as e:
        print(f"❌ 保存照片失败: {e}")

def main():
    """主函数"""
    print("学生拍照系统 - 照片传输测试")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("请输入手机IP地址 (例如: 10.21.4.170): ").strip()
        
    if not ip:
        print("❌ 请提供有效的IP地址")
        return
        
    test_photo_transfer(ip)

if __name__ == '__main__':
    main()
