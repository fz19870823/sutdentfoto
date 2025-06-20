#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手机控制器
负责与Android应用通信
"""

import socket
import threading
import time
import os
import tempfile
from PyQt5.QtCore import QObject, pyqtSignal

class PhoneController(QObject):
    """手机控制器类"""
    
    # 信号定义
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    photo_taken = pyqtSignal(str)  # 照片路径
    error_occurred = pyqtSignal(str)  # 错误信息
    log_message = pyqtSignal(str)  # 日志信息
    
    def __init__(self):
        super().__init__()
        self.socket = None
        self.is_connected_flag = False
        self.phone_ip = ""
        self.phone_port = 8080
        self.photos_dir = os.path.join(tempfile.gettempdir(), "student_photos")
        self._current_photo_uri = None
        self._photo_buffer = bytearray()
        self._expecting_photo_data = False
        self._expected_photo_size = 0
        self._last_progress = -1
        self._unexpected_data_warned = False

        # 创建照片存储目录
        if not os.path.exists(self.photos_dir):
            os.makedirs(self.photos_dir)
            
    def is_connected(self):
        """检查是否已连接"""
        return self.is_connected_flag
        
    def connect_to_phone(self, ip, port):
        """连接到手机"""
        self.phone_ip = ip
        self.phone_port = port
        
        # 在新线程中执行连接
        thread = threading.Thread(target=self._connect_thread)
        thread.daemon = True
        thread.start()
        
    def _connect_thread(self):
        """连接线程"""
        try:
            self.log_message.emit(f"正在连接到 {self.phone_ip}:{self.phone_port}...")
            
            # 创建socket连接
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10秒超时
            
            # 连接到手机
            self.socket.connect((self.phone_ip, self.phone_port))
            
            self.is_connected_flag = True
            self.log_message.emit("连接成功!")
            self.connected.emit()
            
            # 启动接收线程
            receive_thread = threading.Thread(target=self._receive_thread)
            receive_thread.daemon = True
            receive_thread.start()
            
        except socket.timeout:
            self.error_occurred.emit("连接超时，请检查手机IP地址和网络连接")
        except ConnectionRefusedError:
            self.error_occurred.emit("连接被拒绝，请确保手机应用正在运行")
        except Exception as e:
            self.error_occurred.emit(f"连接失败: {str(e)}")
            
    def _receive_thread(self):
        """接收数据线程"""
        try:
            # 设置socket超时，避免阻塞
            self.socket.settimeout(1.0)

            while self.is_connected_flag and self.socket:
                try:
                    # 接收数据
                    data = self.socket.recv(1024)
                    if not data:
                        self.log_message.emit("手机端断开连接")
                        break

                    # 尝试解码为文本消息
                    try:
                        message = data.decode('utf-8').strip()
                        self.log_message.emit(f"收到消息: {message}")

                        # 处理不同类型的消息
                        if message == "CONNECTED":
                            self.log_message.emit("连接确认成功")
                        elif message == "COMMAND_RECEIVED":
                            self.log_message.emit("手机已收到拍照命令")
                        elif message.startswith("PHOTO_TAKEN:"):
                            # 新格式：PHOTO_TAKEN:uri
                            uri = message[12:]  # 去掉"PHOTO_TAKEN:"前缀
                            self.log_message.emit(f"手机拍照完成，照片URI: {uri}")
                            # 准备接收照片数据
                            self._current_photo_uri = uri
                        elif message.startswith("PHOTO_DATA:"):
                            # 照片数据头：PHOTO_DATA:size
                            size_str = message[11:]  # 去掉"PHOTO_DATA:"前缀
                            try:
                                photo_size = int(size_str)
                                self.log_message.emit(f"准备接收照片数据: {photo_size} 字节")
                                self._expecting_photo_data = True
                                self._expected_photo_size = photo_size
                                self._photo_buffer = bytearray()
                            except ValueError:
                                self.log_message.emit(f"无效的照片大小: {size_str}")
                        elif message == "PHOTO_TAKEN":
                            # 兼容旧格式
                            self._handle_photo_taken()
                        elif message == "PONG":
                            self.log_message.emit("心跳响应正常")
                        elif message.startswith("ERROR:"):
                            error_msg = message[6:]  # 去掉"ERROR:"前缀
                            self.error_occurred.emit(f"手机端错误: {error_msg}")
                        else:
                            self.log_message.emit(f"未知消息: {message}")

                    except UnicodeDecodeError:
                        # 这是二进制数据，可能是照片数据的一部分
                        # 首先尝试在数据中查找PHOTO_DATA消息
                        if b"PHOTO_DATA:" in data:
                            # 数据中包含PHOTO_DATA头信息
                            try:
                                text_part = data.decode('utf-8', errors='ignore')
                                if "PHOTO_DATA:" in text_part:
                                    lines = text_part.split('\n')
                                    for line in lines:
                                        if line.startswith("PHOTO_DATA:"):
                                            size_str = line[11:]  # 去掉"PHOTO_DATA:"前缀
                                            try:
                                                photo_size = int(size_str)
                                                self.log_message.emit(f"从混合数据中解析到照片大小: {photo_size} 字节")
                                                self._expecting_photo_data = True
                                                self._expected_photo_size = photo_size
                                                self._photo_buffer = bytearray()
                                                break
                                            except ValueError:
                                                pass
                            except:
                                pass

                        # 如果我们正在等待照片数据，将其添加到缓冲区
                        if self._expecting_photo_data:
                            # 检查数据中是否包含PHOTO_END标记
                            if b"PHOTO_END\n" in data:
                                # 找到结束标记，分离照片数据和结束标记
                                end_marker_pos = data.find(b"PHOTO_END\n")
                                photo_data_part = data[:end_marker_pos]
                                self._photo_buffer.extend(photo_data_part)

                                self.log_message.emit("收到照片结束标记，正在保存...")
                                self._expecting_photo_data = False
                                self._save_received_photo()
                            else:
                                # 普通的照片数据
                                self._photo_buffer.extend(data)
                                progress = (len(self._photo_buffer) / self._expected_photo_size) * 100

                                # 只每10%显示一次进度，避免日志爆表
                                if int(progress) % 10 == 0 and int(progress) != getattr(self, '_last_progress', -1):
                                    self.log_message.emit(f"照片接收进度: {progress:.0f}%")
                                    self._last_progress = int(progress)

                                # 检查是否接收完成（备用检查，主要依靠PHOTO_END标记）
                                if len(self._photo_buffer) >= self._expected_photo_size:
                                    self.log_message.emit("照片数据大小已达到预期，等待结束标记...")
                        else:
                            # 检查是否包含PHOTO_DATA消息（可能混在二进制数据中）
                            if b"PHOTO_DATA:" in data:
                                try:
                                    # 尝试提取PHOTO_DATA信息
                                    data_str = data.decode('utf-8', errors='ignore')
                                    lines = data_str.split('\n')
                                    for line in lines:
                                        if line.startswith("PHOTO_DATA:"):
                                            size_str = line[11:]
                                            try:
                                                photo_size = int(size_str)
                                                self.log_message.emit(f"从混合数据中解析到照片大小: {photo_size} 字节")
                                                self._expecting_photo_data = True
                                                self._expected_photo_size = photo_size
                                                self._photo_buffer = bytearray()

                                                # 检查是否有照片数据在同一个包中
                                                photo_data_start = data.find(b"PHOTO_DATA:")
                                                if photo_data_start >= 0:
                                                    # 找到换行符后的数据
                                                    newline_pos = data.find(b'\n', photo_data_start)
                                                    if newline_pos >= 0:
                                                        remaining_data = data[newline_pos + 1:]
                                                        if remaining_data:
                                                            self._photo_buffer.extend(remaining_data)
                                                            self.log_message.emit(f"同包中包含照片数据: {len(remaining_data)} 字节")
                                                break
                                            except ValueError:
                                                pass
                                except:
                                    pass

                            # 如果仍然没有期待照片数据，显示警告
                            if not self._expecting_photo_data and not getattr(self, '_unexpected_data_warned', False):
                                self.log_message.emit("收到意外的二进制数据，可能是照片数据但未收到大小信息")
                                self._unexpected_data_warned = True

                except socket.timeout:
                    # 超时是正常的，继续循环
                    continue
                except ConnectionResetError:
                    self.log_message.emit("连接被手机端重置")
                    break
                except Exception as e:
                    if self.is_connected_flag:
                        self.log_message.emit(f"接收数据时出错: {str(e)}")
                    break

        except Exception as e:
            if self.is_connected_flag:
                self.error_occurred.emit(f"接收线程错误: {str(e)}")
        finally:
            self._cleanup_connection()



    def _save_received_photo(self):
        """保存接收到的照片"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            photo_filename = f"photo_{timestamp}.jpg"
            photo_path = os.path.join(self.photos_dir, photo_filename)

            # 保存照片数据
            with open(photo_path, 'wb') as f:
                f.write(self._photo_buffer)

            self.log_message.emit(f"照片已保存: {photo_path}")
            self.photo_taken.emit(photo_path)

            # 清理缓冲区
            self._photo_buffer = bytearray()
            self._current_photo_uri = None

        except Exception as e:
            self.error_occurred.emit(f"保存照片失败: {str(e)}")

    def _handle_photo_taken(self, uri=None):
        """处理拍照完成（仅用于兼容旧格式或测试）"""
        self.log_message.emit("收到旧格式拍照通知，创建模拟照片")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        photo_filename = f"photo_{timestamp}_dummy.jpg"
        photo_path = os.path.join(self.photos_dir, photo_filename)

        self._create_dummy_photo(photo_path, uri)
        self.photo_taken.emit(photo_path)
        
    def _create_dummy_photo(self, photo_path, uri=None):
        """创建模拟照片（用于测试）"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # 创建一个800x600的图像
            img = Image.new('RGB', (800, 600))
            img.paste((173, 216, 230), (0, 0, 800, 600))  # lightblue background
            draw = ImageDraw.Draw(img)

            # 添加文本
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            text = f"学生拍照系统\n拍摄时间: {timestamp}\n手机IP: {self.phone_ip}"
            if uri:
                text += f"\n照片URI: {uri}"

            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                # 如果没有找到字体，使用默认字体
                font = ImageFont.load_default()

            # 计算文本位置
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (800 - text_width) // 2
            y = (600 - text_height) // 2

            # 绘制文本
            draw.text((x, y), text, fill='black', font=font)

            # 保存图像
            img.save(photo_path, 'JPEG')

        except ImportError:
            # 如果没有PIL库，创建一个空文件
            with open(photo_path, 'w') as f:
                content = f"模拟照片文件\n拍摄时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n手机IP: {self.phone_ip}"
                if uri:
                    content += f"\n照片URI: {uri}"
                f.write(content)
        except Exception as e:
            self.log_message.emit(f"创建模拟照片失败: {str(e)}")
            
    def take_photo(self):
        """发送拍照命令"""
        if not self.is_connected_flag or not self.socket:
            self.error_occurred.emit("未连接到手机")
            return
            
        try:
            # 发送拍照命令
            command = "TAKE_PHOTO"
            self.socket.send(command.encode('utf-8'))
            self.log_message.emit("已发送拍照命令")
            
        except Exception as e:
            self.error_occurred.emit(f"发送拍照命令失败: {str(e)}")
            
    def send_ping(self):
        """发送心跳包"""
        if not self.is_connected_flag or not self.socket:
            return False

        try:
            self.socket.send("PING".encode('utf-8'))
            return True
        except Exception as e:
            self.log_message.emit(f"发送心跳失败: {str(e)}")
            return False

    def disconnect(self):
        """断开连接"""
        if not self.is_connected_flag:
            self.log_message.emit("已经处于断开状态")
            return

        self.log_message.emit("正在断开连接...")

        # 发送断开连接命令
        if self.socket:
            try:
                self.socket.send("DISCONNECT".encode('utf-8'))
                time.sleep(0.1)  # 给手机端一点时间处理
            except:
                pass

        self.is_connected_flag = False
        self._cleanup_connection()
        
    def _cleanup_connection(self):
        """清理连接"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        if self.is_connected_flag:
            self.is_connected_flag = False
            self.log_message.emit("连接已断开")
            self.disconnected.emit()

        # 重置照片接收状态
        self._expecting_photo_data = False
        self._expected_photo_size = 0
        self._photo_buffer = bytearray()
        self._last_progress = -1
        self._unexpected_data_warned = False
            
    def get_photos_directory(self):
        """获取照片存储目录"""
        return self.photos_dir
