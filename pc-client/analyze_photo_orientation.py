#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析照片方向信息
"""

import socket
import time
import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS

def analyze_photo_orientation(ip, port=8080):
    """分析照片方向信息"""
    print(f"🔍 分析照片方向 - 连接到 {ip}:{port}")
    
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
        
        # 接收照片数据
        photo_uri = None
        photo_size = None
        received_data = bytearray()
        
        while True:
            try:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                
                # 尝试解码为文本
                try:
                    text = chunk.decode('utf-8')
                    lines = text.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if line == "COMMAND_RECEIVED":
                            print("✅ 拍照命令已确认")
                        elif line.startswith("PHOTO_TAKEN:"):
                            photo_uri = line[12:]
                            print(f"📷 拍照完成: {photo_uri}")
                        elif line.startswith("PHOTO_DATA:"):
                            photo_size = int(line[11:])
                            print(f"📊 照片大小: {photo_size} 字节")
                            print("🔄 开始接收照片数据...")
                            received_data = bytearray()
                        elif line == "PHOTO_END":
                            print("🏁 收到照片结束标记")
                            analyze_and_save_photo(received_data, photo_uri, photo_size)
                            return
                            
                except UnicodeDecodeError:
                    # 二进制照片数据
                    if b"PHOTO_END" in chunk:
                        # 找到结束位置
                        end_pos = chunk.find(b"PHOTO_END")
                        photo_data_part = chunk[:end_pos]
                        received_data.extend(photo_data_part)
                        print("🏁 照片数据接收完成")
                        analyze_and_save_photo(received_data, photo_uri, photo_size)
                        return
                    else:
                        # 普通照片数据
                        received_data.extend(chunk)
                        if photo_size:
                            progress = (len(received_data) / photo_size) * 100
                            if int(progress) % 20 == 0:  # 每20%显示一次
                                print(f"📈 接收进度: {progress:.0f}%")
                
            except socket.timeout:
                print("⏰ 接收超时")
                break
            except Exception as e:
                print(f"❌ 接收错误: {e}")
                break
                
        sock.close()
        
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def analyze_and_save_photo(photo_data, uri=None, expected_size=None):
    """分析并保存照片"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"analyze_photo_{timestamp}.jpg"
        
        print(f"💾 保存照片: {filename}")
        print(f"📏 实际大小: {len(photo_data)} 字节")
        if expected_size:
            print(f"📏 预期大小: {expected_size} 字节")
        
        # 保存文件
        with open(filename, 'wb') as f:
            f.write(photo_data)
        
        # 分析照片信息
        try:
            img = Image.open(filename)
            print(f"🖼️ 图片尺寸: {img.size}")
            print(f"🎨 图片格式: {img.format}")
            print(f"🎭 图片模式: {img.mode}")
            
            # 分析EXIF信息
            try:
                exif = img.getexif()
                if exif:
                    print("📋 EXIF信息:")

                    # 查找方向信息 (tag 274 是Orientation)
                    orientation = exif.get(274, None)
                else:
                    print("📋 EXIF信息: 无EXIF数据")
                    orientation = None
                
                if orientation:
                    orientation_desc = {
                        1: "正常 (0°)",
                        2: "水平翻转",
                        3: "旋转180°",
                        4: "垂直翻转",
                        5: "水平翻转 + 逆时针90°",
                        6: "顺时针90°",
                        7: "水平翻转 + 顺时针90°",
                        8: "逆时针90°"
                    }
                    print(f"🧭 EXIF方向: {orientation} - {orientation_desc.get(orientation, '未知')}")
                else:
                    print("🧭 EXIF方向: 未找到方向信息")

                # 显示其他重要EXIF信息
                important_tags = [
                    (274, "Orientation"),
                    (271, "Make"),
                    (272, "Model"),
                    (306, "DateTime"),
                ]

                for tag_id, tag_name in important_tags:
                    if tag_id in exif:
                        print(f"   {tag_name}: {exif[tag_id]}")

            except Exception as e:
                print(f"📋 EXIF信息读取失败: {e}")
                orientation = None
            
            # 测试不同的显示方向
            print("\n🔄 测试不同方向的显示效果:")
            
            # 原始图片
            print(f"   原始: {img.size}")
            
            # 旋转90度
            rotated_90 = img.rotate(-90, expand=True)
            print(f"   逆时针90°: {rotated_90.size}")
            
            # 旋转180度
            rotated_180 = img.rotate(180, expand=True)
            print(f"   旋转180°: {rotated_180.size}")
            
            # 旋转270度
            rotated_270 = img.rotate(90, expand=True)
            print(f"   顺时针90°: {rotated_270.size}")
            
            img.close()
            rotated_90.close()
            rotated_180.close()
            rotated_270.close()
            
        except Exception as e:
            print(f"❌ 图片分析失败: {e}")
            
    except Exception as e:
        print(f"❌ 保存失败: {e}")

def main():
    """主函数"""
    print("🔍 学生拍照系统 - 照片方向分析工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("请输入手机IP地址: ").strip()
        
    if not ip:
        print("❌ 请提供有效的IP地址")
        return
        
    analyze_photo_orientation(ip)

if __name__ == '__main__':
    main()
