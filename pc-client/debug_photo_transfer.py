#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试照片传输 - 分析数据结构
"""

import socket
import time
import sys
import os

def debug_photo_transfer(ip, port=8080):
    """调试照片传输，详细分析数据结构"""
    print(f"🔍 调试模式：连接到 {ip}:{port}")
    
    try:
        # 创建socket连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((ip, port))
        
        print("✅ 连接成功!")
        
        # 接收连接确认
        data = sock.recv(1024)
        message = data.decode('utf-8').strip()
        print(f"📨 收到: {message}")
        
        # 发送拍照命令
        print("📸 发送拍照命令...")
        sock.send("TAKE_PHOTO".encode('utf-8'))
        
        # 调试数据接收
        photo_uri = None
        photo_size = None
        received_data = bytearray()
        message_buffer = ""
        
        print("🔍 开始调试数据接收...")
        
        while True:
            try:
                chunk = sock.recv(1024)
                if not chunk:
                    print("❌ 连接断开")
                    break
                
                print(f"📦 收到数据块: {len(chunk)} 字节")
                
                # 尝试解码为文本
                try:
                    text = chunk.decode('utf-8')
                    print(f"📝 文本内容: {repr(text)}")
                    
                    # 处理消息
                    message_buffer += text
                    lines = message_buffer.split('\n')
                    message_buffer = lines[-1]  # 保留未完成的行
                    
                    for line in lines[:-1]:
                        line = line.strip()
                        if line:
                            print(f"📋 处理消息: {repr(line)}")
                            
                            if line == "COMMAND_RECEIVED":
                                print("✅ 拍照命令已确认")
                            elif line.startswith("PHOTO_TAKEN:"):
                                photo_uri = line[12:]
                                print(f"📷 拍照完成: {photo_uri}")
                            elif line.startswith("PHOTO_DATA:"):
                                photo_size = int(line[11:])
                                print(f"📊 照片大小: {photo_size} 字节")
                                print("🔄 开始接收照片数据...")
                                
                                # 开始接收照片数据
                                received_data = bytearray()
                                break
                            elif line == "PHOTO_END":
                                print("🏁 收到照片结束标记")
                                save_debug_photo(received_data, photo_uri, photo_size)
                                return
                                
                except UnicodeDecodeError:
                    print(f"📦 二进制数据: {len(chunk)} 字节")
                    print(f"🔍 前16字节: {chunk[:16].hex()}")
                    
                    # 检查是否包含文本标记
                    if b"PHOTO_DATA:" in chunk:
                        print("🔍 在二进制数据中发现PHOTO_DATA标记")
                        # 分离文本和二进制部分
                        text_part = chunk.decode('utf-8', errors='ignore')
                        print(f"📝 混合数据文本部分: {repr(text_part)}")
                    
                    if b"PHOTO_END" in chunk:
                        print("🔍 在二进制数据中发现PHOTO_END标记")
                        # 找到结束位置
                        end_pos = chunk.find(b"PHOTO_END")
                        photo_data_part = chunk[:end_pos]
                        received_data.extend(photo_data_part)
                        print(f"🏁 照片数据接收完成: {len(received_data)} 字节")
                        save_debug_photo(received_data, photo_uri, photo_size)
                        return
                    
                    # 如果正在接收照片数据
                    if photo_size is not None:
                        received_data.extend(chunk)
                        progress = (len(received_data) / photo_size) * 100
                        print(f"📈 接收进度: {progress:.1f}% ({len(received_data)}/{photo_size})")
                        
                        if len(received_data) >= photo_size:
                            print("⚠️ 接收数据已达到预期大小，但未收到结束标记")
                            save_debug_photo(received_data, photo_uri, photo_size)
                            return
                
            except socket.timeout:
                print("⏰ 接收超时")
                break
            except Exception as e:
                print(f"❌ 接收错误: {e}")
                break
                
        sock.close()
        
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def save_debug_photo(photo_data, uri=None, expected_size=None):
    """保存调试照片并分析"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"debug_photo_{timestamp}.jpg"
        
        print(f"💾 保存调试照片: {filename}")
        print(f"📏 实际大小: {len(photo_data)} 字节")
        if expected_size:
            print(f"📏 预期大小: {expected_size} 字节")
            if len(photo_data) != expected_size:
                print(f"⚠️ 大小不匹配! 差异: {len(photo_data) - expected_size} 字节")
        
        # 分析文件头
        if len(photo_data) >= 16:
            header = photo_data[:16]
            print(f"🔍 文件头 (hex): {header.hex()}")
            print(f"🔍 文件头 (ascii): {header}")
            
            # 检查JPEG文件头
            if photo_data[:2] == b'\xff\xd8':
                print("✅ 检测到有效的JPEG文件头")
            else:
                print("❌ 无效的JPEG文件头!")
                print(f"   期望: ff d8")
                print(f"   实际: {photo_data[:2].hex()}")
        
        # 分析文件尾
        if len(photo_data) >= 16:
            tail = photo_data[-16:]
            print(f"🔍 文件尾 (hex): {tail.hex()}")
            print(f"🔍 文件尾 (ascii): {tail}")
            
            # 检查JPEG文件尾
            if photo_data[-2:] == b'\xff\xd9':
                print("✅ 检测到有效的JPEG文件尾")
            else:
                print("❌ 无效的JPEG文件尾!")
                print(f"   期望: ff d9")
                print(f"   实际: {photo_data[-2:].hex()}")
        
        # 保存文件
        with open(filename, 'wb') as f:
            f.write(photo_data)
        
        print(f"💾 文件已保存: {filename}")
        
        # 尝试验证文件
        try:
            from PIL import Image
            img = Image.open(filename)
            print(f"✅ PIL验证成功: {img.size}, {img.format}")
        except Exception as e:
            print(f"❌ PIL验证失败: {e}")
            
    except Exception as e:
        print(f"❌ 保存失败: {e}")

def main():
    """主函数"""
    print("🔍 学生拍照系统 - 照片传输调试工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("请输入手机IP地址: ").strip()
        
    if not ip:
        print("❌ 请提供有效的IP地址")
        return
        
    debug_photo_transfer(ip)

if __name__ == '__main__':
    main()
