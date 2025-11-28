#!/usr/bin/env python3
"""
Openterface 服务端模拟器
模拟server模块中的TCP server，只处理lastImage指令
"""

import socket
import threading
import os
import sys
from datetime import datetime


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
            # 固定图片路径
            image_path = r"C:\Users\huang\Pictures\openterface\1.jpg"
            
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

def start_server(host='localhost', port=12345):
    """
    启动TCP服务器
    
    Args:
        host (str): 服务器主机地址
        port (int): 服务器端口
    """
    # 创建TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # 绑定地址和端口
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"🚀 服务器已在 {host}:{port} 启动")
        print("🔧 仅处理 lastimage 命令")
        print("⏳ 等待客户端连接...")
        print("💡 请使用客户端连接测试")
        
        while True:
            # 接受客户端连接
            client_socket, address = server_socket.accept()
            
            # 为每个客户端创建新线程
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True
            client_thread.start()
            
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
    HOST = 'localhost'
    PORT = 12345
    
    print("=" * 50)
    print("🔧 Openterface 服务端模拟器")
    print("=" * 50)
    print("功能:")
    print("  - 模拟TCP服务器")
    print("  - 仅处理 lastimage 命令")
    print("  - 读取固定图片文件")
    print("  - 图片路径: C:\\Users\\huang\\Pictures\\openterface\\1.jpg")
    print("-")
    print("使用方法:")
    print("  1. 运行此程序启动服务器")
    print("  2. 使用支持TCP连接的客户端测试")
    print("  3. 客户端发送 'lastimage' 命令")
    print("  4. 服务器返回图片数据")
    print("-")
    
    # 启动服务器
    start_server(HOST, PORT)
