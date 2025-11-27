#!/usr/bin/env python3
"""
Openterface AI Chat Client
与本地OpenAI兼容API进行交互的智能对话客户端
"""

import requests
import json
import os
import socket
import datetime
from typing import Dict, Any, Optional

def get_api_response(prompt: str, api_url: str = "http://localhost:8000/v1/chat/completions", model: str = "default", image_path: str = None) -> str:
    """
    向本地OpenAI兼容API发送请求并获取响应
    
    Args:
        prompt (str): 用户的问题或提示
        api_url (str): API端点URL
        model (str): 使用的模型名称
        image_path (str): 图片文件路径（可选）
        
    Returns:
        str: API响应内容
    """
    try:
        # 构造请求体 - 支持不同API格式
        if "/chat" in api_url or "chat" in api_url.lower():
            # Chat API 格式
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # 如果提供了图片，则将其作为多模态内容添加
            if image_path and os.path.exists(image_path):
                # 添加图像内容到消息中
                messages[0]["content"] = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_to_base64(image_path)}"}}
                ]
            
            payload = {
                "messages": messages,
                "max_tokens": 4096,
                # "temperature": 0.7,
                # "top_p": 1,
                "model": model
            }
        else:
            # Completions API 格式
            payload = {
                "prompt": prompt,
                "max_tokens": 4096,
                # "temperature": 0.7,
                # "top_p": 1,
                # "frequency_penalty": 0,
                # "presence_penalty": 0,
                "model": model
            }
        
        # 获取API密钥，从环境变量获取，如果没有则使用默认值"EMPTY"
        api_key = os.getenv("API_KEY", "EMPTY")
        
        # 发送POST请求
        response = requests.post(
            api_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            timeout=30
        )
        
        # 检查响应状态
        if response.status_code == 200:
            data = response.json()
            # 根据不同API返回格式提取响应内容
            if "choices" in data and len(data["choices"]) > 0:
                # 对于OpenAI兼容API
                choice = data["choices"][0]
                if "text" in choice:
                    return choice["text"].strip()
                elif "message" in choice:
                    # 对于Chat接口
                    return choice["message"]["content"].strip()
                elif "delta" in choice:
                    # 流式响应处理
                    return choice["delta"].get("content", "").strip()
                else:
                    return json.dumps(choice, indent=2, ensure_ascii=False)
            else:
                return "未找到有效响应内容"
        else:
            return f"API请求失败，状态码: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "❌ 请求超时，请检查本地API服务是否运行正常"
    except requests.exceptions.ConnectionError:
        return "❌ 无法连接到本地API服务，请确保API服务正在运行"
    except Exception as e:
        return f"❌ 发生错误: {str(e)}"


def encode_image_to_base64(image_path: str) -> str:
    """
    将图像文件编码为base64字符串
    
    Args:
        image_path (str): 图像文件路径
        
    Returns:
        str: Base64编码的图像数据
    """
    import base64
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        return f"图像编码错误: {str(e)}"


def test_api_connection(api_url: str) -> bool:
    """
    测试API连接是否正常
    
    Args:
        api_url (str): API端点URL
        
    Returns:
        bool: 连接是否成功
    """
    try:
        # 尝试获取模型列表
        models_endpoint = api_url.replace("/chat/completions", "/models")
        test_response = requests.get(models_endpoint, timeout=5)
        return test_response.status_code == 200
    except:
        return False


def print_header():
    """打印程序标题和帮助信息"""
    print("=" * 60)
    print("🤖 Openterface AI Chat 客户端")
    print("与本地OpenAI兼容API进行交互的智能对话系统")
    print("=" * 60)
    print("💡 功能特点:")
    print("   • 与本地大模型实时对话")
    print("   • 支持多种API格式")
    print("   • 友好的交互界面")
    print("   • 错误处理和重试机制")
    print("=" * 60)


def print_help():
    """打印帮助信息"""
    print("\n📋 帮助信息:")
    print("  • 输入任何问题与AI对话")
    print("  • 输入 'quit' 或 'exit' 退出程序")
    print("  • 输入 'clear' 清除对话历史")
    print("  • 输入 'help' 查看帮助信息")
    print("  • 输入 'info' 查看当前API配置")
    print("  • 输入 'model' 切换模型")
    print("  • 输入 'image' 从服务器获取最新图片并进行多模态问答")
    print("=" * 60)


def print_api_info(api_url: str):
    """打印API信息"""
    print(f"\n📡 当前API配置:")
    print(f"   地址: {api_url}")
    connection_status = "✅ 可用" if test_api_connection(api_url) else "⚠️  不可用"
    print(f"   状态: {connection_status}")



def get_last_image_from_server(host: str = 'localhost', port: int = 12345, output_dir: str = './images', timeout: int = 60) -> str:
    """
    从Openterface服务器获取最新的图片
    
    Args:
        host (str): 服务器地址
        port (int): 服务器端口
        output_dir (str): 图片保存目录
        timeout (int): 连接超时时间(秒)
        
    Returns:
        str: 图片文件路径或错误信息
    """
    try:
        # 创建保存目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 日志函数
        def log(message):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")
        
        log("开始连接到Openterface服务器...")
        log(f"目标: {host}:{port}")
        
        # 创建TCP连接
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(timeout)  # 设置超时
        
        # 连接到服务器
        client_socket.connect((host, port))
        log(f"✅ 成功连接到服务器 {host}:{port}")
        
        # 发送"lastimage"命令
        command = "lastimage"
        client_socket.send(command.encode('utf-8'))
        log(f"📤 已发送命令: {command}")
        
        # 接收响应
        response = b""
        total_received = 0
        expected_image_size = 0
        
        # 先读取头部信息
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data
                total_received += len(data)
                
                # 如果收到的是图片数据，尝试解析头部信息
                if response.startswith(b"IMAGE:") and b'\n' in response:
                    # 解析图片大小
                    header_end = response.find(b'\n')
                    if header_end != -1:
                        image_size_str = response[6:header_end].decode('utf-8')
                        expected_image_size = int(image_size_str)
                        break
                elif b"ERROR:" in response or b"STATUS:" in response:
                    # 如果是错误或状态响应，立即停止接收
                    break
            except socket.timeout:
                log("⏰ 接收超时，可能数据不完整")
                break
            except Exception as e:
                log(f"❌ 接收数据时出错: {str(e)}")
                break
        
        # 继续接收剩余的图像数据
        if expected_image_size > 0:
            expected_total = 6 + len(str(expected_image_size)) + 1 + expected_image_size  # 头部 + 换行符 + 图像数据大小
            while len(response) < expected_total and total_received < expected_total + 10000:  # 添加一些容错
                try:
                    data = client_socket.recv(min(4096, expected_total - len(response)))
                    if not data:
                        break
                    response += data
                    total_received += len(data)
                except socket.timeout:
                    log("⏰ 图像数据接收超时")
                    break
                except Exception as e:
                    log(f"❌ 接收图像数据时出错: {str(e)}")
                    break
        
        log(f"📥 收到响应，大小: {len(response)} 字节")
        
        # 检查是否是图片数据
        if response.startswith(b"IMAGE:"):
            # 解析图片数据
            try:
                # 分离图片大小信息和实际图片数据
                header_end = response.find(b'\n')
                if header_end != -1:
                    image_size_str = response[6:header_end].decode('utf-8')
                    image_size = int(image_size_str)
                    image_data = response[header_end+1:]
                    
                    # 验证数据完整性
                    if len(image_data) >= image_size:
                        # 生成文件名
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"last_image_{timestamp}.jpg"
                        filepath = os.path.join(output_dir, filename)
                        
                        # 保存图片到文件
                        with open(filepath, 'wb') as f:
                            f.write(image_data[:image_size])
                        
                        log(f"💾 图片已保存到: {filepath}")
                        log(f"📊 图片大小: {image_size} 字节")
                        
                        # 显示成功信息
                        print("\n✅ 图片获取成功!")
                        print(f"📁 文件路径: {filepath}")
                        print(f"📊 文件大小: {image_size} 字节")
                        print(f"🕐 保存时间: {timestamp}")
                        
                        # 关闭连接
                        client_socket.close()
                        return filepath
                        
            except ValueError as ve:
                log(f"❌ 图片数据格式错误: {str(ve)}")
            except Exception as e:
                log(f"❌ 处理图片数据时出错: {str(e)}")
        
        # 检查是否是错误响应
        elif response.startswith(b"ERROR:"):
            error_msg = response.decode('utf-8')[6:].strip()
            log(f"❌ 服务器错误: {error_msg}")
            client_socket.close()
            return f"❌ 服务器错误: {error_msg}"
            
        # 检查是否是状态响应
        elif response.startswith(b"STATUS:"):
            status_msg = response.decode('utf-8')[7:].strip()
            log(f"📈 服务器状态: {status_msg}")
            client_socket.close()
            return f"📈 服务器状态: {status_msg}"
            
        else:
            # 未知响应格式
            log(f"⚠️  收到未知响应格式: {response[:100]}...")
            # 尝试显示文本内容
            try:
                text_content = response.decode('utf-8', errors='ignore')
                if text_content.strip():
                    log(f"文本内容: {text_content[:200]}...")
            except:
                pass
        
        # 关闭连接
        client_socket.close()
        log("🔒 连接已关闭")
        return "❌ 图片获取失败"
        
    except socket.timeout:
        log("⏰ 连接超时")
        return "❌ 连接超时"
    except ConnectionRefusedError:
        log("❌ 连接被拒绝，请确保服务器正在运行")
        return "❌ 连接被拒绝，请确保服务器正在运行"
    except socket.gaierror as e:
        log(f"🌐 DNS解析错误: {str(e)}")
        return f"🌐 DNS解析错误: {str(e)}"
    except Exception as e:
        log(f"💥 发生未知错误: {str(e)}")
        return f"💥 发生未知错误: {str(e)}"


def main():
    """主函数：提供交互式对话界面"""
    print_header()
    
    # 默认API地址
    api_url = "http://localhost:8000/v1/chat/completions"
    model = "qwen3-30b-vl"
    
    # 获取用户输入的API地址（可选）
    print(f"\n🔧 配置API连接:")
    print(f"   默认地址: {api_url}")
    custom_api = input("   请输入自定义API地址 (直接回车使用默认地址): ").strip()
    if custom_api:
        api_url = custom_api
    
    # 获取用户输入的模型名称（可选）
    print(f"   默认模型: {model}")
    custom_model = input("   请输入自定义模型名称 (直接回车使用默认模型): ").strip()
    if custom_model:
        model = custom_model
    
    # 测试连接
    print(f"\n🔗 正在连接到 {api_url}...")
    if test_api_connection(api_url):
        print("   ✅ 成功连接到本地API服务")
    else:
        print("   ⚠️  API服务可能运行但未正确响应")
        print("   请确保本地API服务正在运行")
    
    print("\n" + "-" * 60)
    print("💬 开始对话 (输入 'help' 查看帮助)")
    print("-" * 60)
    
    # 交互式对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 您的问题: ").strip()
            
            # 处理各种命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！感谢使用 Openterface AI Chat 客户端")
                break
            
            # 处理清除命令
            if user_input.lower() in ['clear', 'cls']:
                print("\n🔄 对话历史已清除")
                continue
            
            # 处理帮助命令
            if user_input.lower() == 'help':
                print_help()
                continue
            
            # 处理信息命令
            if user_input.lower() == 'info':
                print_api_info(api_url)
                continue
            
            # 处理模型切换命令
            if user_input.lower() == 'model':
                new_model = input("   请输入模型名称 (直接回车保持默认): ").strip()
                if new_model:
                    model = new_model
                    print(f"   ✅ 模型已切换为: {model}")
                continue
            
            # 处理图像命令
            if user_input.lower() == 'image':
                # 从服务器获取图片
                print("\n📥 正在从服务器获取最新图片...")
                image_path = get_last_image_from_server()
                print(f"   🔍 服务器响应: {image_path}")
                if image_path and image_path.startswith("./images"):
                    print(f"   📷 已获取图片: {os.path.basename(image_path)}")
                    # 明确提示用户输入问题
                    question = input("   请输入要询问的问题: ").strip()
                    if not question:
                        print("   ⚠️  问题不能为空")
                        continue
                    # 发送带图像和问题的请求
                    print("\n🧠 正在处理您的问题...")
                    print("   🔄 请稍候...")
                    response = get_api_response(question, api_url, model, image_path)
                else:
                    if "❌" in image_path:
                        print(f"   ⚠️ {image_path}")
                        # 重新提示用户输入其他内容
                        continue
                    # 发送普通请求
                    print("\n🧠 正在处理您的问题...")
                    print("   🔄 请稍候...")
                    response = get_api_response(user_input, api_url, model)
            else:
                # 处理空输入
                if not user_input:
                    print("⚠️  请输入有效的问题")
                    continue
                
                # 发送请求并显示响应
                print("\n🧠 正在处理您的问题...")
                print("   🔄 请稍候...")
                
                # 获取响应
                response = get_api_response(user_input, api_url, model)
            
            # 显示响应
            print("\n🤖 AI响应:")
            print("-" * 40)
            print(response)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            print("请重试或检查API服务状态")


if __name__ == "__main__":
    main()