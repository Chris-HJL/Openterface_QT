#!/usr/bin/env python3
"""
Openterface 服务端模拟器
模拟server模块中的TCP server，处理lastImage指令
支持通过HTTP接口更新图片路径
"""

import socket
import threading
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

# 全局变量，存储当前图片路径
current_image_path = r"C:\Users\huang\Pictures\openterface\1.jpg"
image_path_lock = threading.Lock()


def read_image_file(file_path):
    """
    读取指定的图片文件
    
    Args:
        file_path (str): 图片文件路径
        
    Returns:
        bytes: 图片文件的二进制数据
    """
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"读取图片文件时出错: {e}")
        return None

def handle_client(client_socket, address):
    """
    处理客户端连接
    
    Args:
        client_socket: 客户端socket连接
        address: 客户端地址
    """
    print(f"✅ 客户端 {address} 已连接")
    
    try:
        # 接收客户端发送的命令
        command = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()
        print(f"📥 收到命令: {command}")
        
        # 只处理lastimage命令
        if command.lower() == "lastimage":
            # 使用全局图片路径
            with image_path_lock:
                image_path = current_image_path
            
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                error_msg = f"图片文件不存在: {image_path}"
                client_socket.send(f"ERROR: {error_msg}\n".encode('utf-8'))
                print(f"❌ {error_msg}")
            else:
                # 读取图片文件
                image_data = read_image_file(image_path)
                if image_data is None:
                    error_msg = "无法读取图片文件"
                    client_socket.send(f"ERROR: {error_msg}\n".encode('utf-8'))
                    print(f"❌ {error_msg}")
                else:
                    # 发送图片数据给客户端 - 使用正确的二进制格式
                    image_size = len(image_data)
                    # 先发送头部信息，确保以换行符结尾
                    header = f"IMAGE:{image_size}\n"
                    client_socket.send(header.encode('utf-8'))
                    # 再发送图片数据 - 确保是完整的二进制数据
                    client_socket.send(image_data)
                    print(f"📤 已发送图片，大小: {image_size} 字节")
                    print(f"✅ 图片传输完成")
        else:
            # 不支持的命令
            error_msg = f"不支持的命令: {command}"
            client_socket.send(f"ERROR: {error_msg}\n".encode('utf-8'))
            print(f"❌ {error_msg}")
            
    except Exception as e:
        print(f"处理客户端请求时出错: {e}")
        import traceback
        traceback.print_exc()
        client_socket.send(f"ERROR: 处理请求时出错\n".encode('utf-8'))
    finally:
        try:
            client_socket.close()
            print(f"🔒 客户端 {address} 连接已关闭")
        except:
            pass

class ImagePathHandler(BaseHTTPRequestHandler):
    """HTTP请求处理类，用于更新图片路径"""
    
    def do_GET(self):
        """处理GET请求，返回当前图片路径"""
        if self.path == '/image-path':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            with image_path_lock:
                response = {
                    'status': 'success',
                    'image_path': current_image_path,
                    'exists': os.path.exists(current_image_path)
                }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        """处理POST请求，更新图片路径"""
        if self.path == '/image-path':
            try:
                # 获取请求体长度
                content_length = int(self.headers.get('Content-Length', 0))
                
                # 读取请求体
                post_data = self.rfile.read(content_length).decode('utf-8')
                print(f"📥 收到POST数据: {post_data}")
                
                # 尝试多种解析方式
                new_path = None
                
                # 方法1: 解析URL编码的表单数据
                try:
                    parsed_data = urllib.parse.parse_qs(post_data)
                    new_path = parsed_data.get('path', [None])[0]
                    if new_path:
                        print(f"📝 方法1成功解析到路径: {new_path}")
                except:
                    pass
                
                # 方法2: 直接解析 "path=VALUE" 格式
                if not new_path and post_data.startswith('path='):
                    new_path = post_data[5:]  # 去掉 "path=" 前缀
                    print(f"📝 方法2成功解析到路径: {new_path}")
                
                # 方法3: 处理JSON格式
                if not new_path:
                    try:
                        json_data = json.loads(post_data)
                        new_path = json_data.get('path')
                        if new_path:
                            print(f"📝 方法3成功解析到路径: {new_path}")
                    except:
                        pass
                
                if new_path:
                    # 更新全局图片路径
                    global current_image_path
                    with image_path_lock:
                        current_image_path = new_path
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    response = {
                        'status': 'success',
                        'message': f'图片路径已更新为: {new_path}',
                        'path': new_path
                    }
                    print(f"📝 图片路径已更新为: {new_path}")
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    response = {
                        'status': 'error',
                        'message': '缺少path参数'
                    }
                
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                response = {
                    'status': 'error',
                    'message': f'处理请求时出错: {str(e)}'
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """重写日志方法，避免输出到控制台"""
        pass

def start_http_server(host='localhost', port=8080, stop_event=None):
    """启动HTTP服务器"""
    try:
        http_server = HTTPServer((host, port), ImagePathHandler)
        print(f"🌐 HTTP服务器已在 {host}:{port} 启动")
        print(f"   查询当前路径: curl http://{host}:{port}/image-path")
        print(f"   更新图片路径:")
        print(f"     直接格式: curl -d \"path=C:\\\\path\\\\to\\\\image.jpg\" http://{host}:{port}/image-path")
        print(f"     JSON格式: curl -d '{{\"path\": \"C:\\\\path\\\\to\\\\image.jpg\"}}' http://{host}:{port}/image-path")
        
        # 设置超时以便定期检查stop_event
        http_server.timeout = 0.5
        while not (stop_event and stop_event.is_set()):
            http_server.handle_request()
        
        print("🌐 HTTP服务器已停止")
    except Exception as e:
        print(f"HTTP服务器启动失败: {e}")

def start_server(host='localhost', port=12345, stop_event=None):
    """
    启动TCP服务器
    
    Args:
        host (str): 服务器主机地址
        port (int): 服务器端口
        stop_event: 停止事件
    """
    # 创建TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 设置socket超时，以便定期检查stop_event
    server_socket.settimeout(1.0)
    
    try:
        # 绑定地址和端口
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"🚀 服务器已在 {host}:{port} 启动")
        print("🔧 仅处理 lastimage 命令")
        print("⏳ 等待客户端连接...")
        print("💡 请使用客户端连接测试")
        
        while not (stop_event and stop_event.is_set()):
            try:
                # 接受客户端连接（带超时）
                client_socket, address = server_socket.accept()
                
                # 为每个客户端创建新线程
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                # 超时异常，继续循环检查stop_event
                continue
            
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"服务器运行时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            server_socket.close()
        except:
            pass

if __name__ == "__main__":
    # 默认配置
    TCP_HOST = 'localhost'
    TCP_PORT = 12345
    HTTP_HOST = 'localhost'
    HTTP_PORT = 8080
    
    print("=" * 50)
    print("🔧 Openterface 服务端模拟器")
    print("=" * 50)
    print("功能:")
    print("  - 模拟TCP服务器")
    print("  - 处理 lastimage 命令")
    print("  - 支持动态更新图片路径")
    print("  - 提供HTTP接口用于路径管理")
    print("  - 支持多种数据格式（直接格式、URL编码、JSON）")
    print("  - UTF-8编码支持，中文字符正常显示")
    print("-")
    print("TCP服务器:")
    print(f"  - 地址: {TCP_HOST}:{TCP_PORT}")
    print("  - 命令: lastimage")
    print("-")
    print("HTTP服务器:")
    print(f"  - 地址: http://{HTTP_HOST}:{HTTP_PORT}")
    print("  - 查询路径: curl http://localhost:8080/image-path")
    print("  - 更新路径:")
    print("    - 直接格式: curl -d \"path=C:\\path\\to\\image.jpg\" http://localhost:8080/image-path")
    print("    - JSON格式: curl -d '{\"path\": \"C:\\\\path\\\\to\\\\image.jpg\"}' http://localhost:8080/image-path")
    print("-")
    print("当前图片路径:")
    print(f"  - {current_image_path}")
    print("-")
    
    try:
        # 创建停止事件，用于通知服务器停止
        stop_event = threading.Event()
        
        # 启动HTTP服务器（在新线程中）
        http_thread = threading.Thread(
            target=start_http_server,
            args=(HTTP_HOST, HTTP_PORT, stop_event),
            daemon=True
        )
        http_thread.start()
        
        # 启动TCP服务器（在主线程中）
        start_server(TCP_HOST, TCP_PORT, stop_event)
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止所有服务器...")
        # 设置停止事件，通知服务器停止
        stop_event.set()
        print("✅ 所有服务器已停止")
    except Exception as e:
        print(f"服务器运行时出错: {e}")
        import traceback
        traceback.print_exc()
