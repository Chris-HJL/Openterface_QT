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

# 全局变量，用于存储对话历史
conversation_history = []
is_multiturn_mode = False

# 多语言支持全局变量
current_translations = {}
current_language = "en"

def load_translations(lang_code: str = "en") -> Dict[str, Any]:
    """
    加载指定语言的翻译文件
    
    Args:
        lang_code (str): 语言代码，如 "zh" 或 "en"
        
    Returns:
        Dict[str, Any]: 翻译字典
    """
    try:
        lang_file = os.path.join("i18n", f"{lang_code}.json")
        with open(lang_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果指定语言文件不存在，加载默认语言（英语）
        with open(os.path.join("i18n", "en.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load translation file: {str(e)}")
        return {}

def _(key: str, **kwargs) -> str:
    """
    翻译函数，支持格式化字符串
    
    Args:
        key (str): 翻译键
        **kwargs: 格式化参数
        
    Returns:
        str: 翻译后的文本
    """
    global current_translations
    # 支持嵌套键，如 "messages.connecting"
    keys = key.split(".")
    value = current_translations
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return key  # 如果键不存在，返回原始键
    
    # 支持格式化字符串
    if kwargs and isinstance(value, str):
        return value.format(**kwargs)
    return value

def switch_language(lang_code: str) -> bool:
    """
    切换语言
    
    Args:
        lang_code (str): 语言代码，如 "zh" 或 "en"
        
    Returns:
        bool: 是否切换成功
    """
    global current_translations, current_language
    if lang_code in ["zh", "en"]:
        new_translations = load_translations(lang_code)
        if new_translations:
            current_translations = new_translations
            current_language = lang_code
            print(_("messages.lang_switched", lang=lang_code))
            return True
    return False

def get_api_response(prompt: str, api_url: str = "http://localhost:8000/v1/chat/completions", model: str = "default", image_path: str = None, history: list = None) -> str:
    """
    向本地OpenAI兼容API发送请求并获取响应
    
    Args:
        prompt (str): 用户的问题或提示
        api_url (str): API端点URL
        model (str): 使用的模型名称
        image_path (str): 图片文件路径（可选）
        history (list): 对话历史记录（可选）
        
    Returns:
        str: API响应内容
    """
    try:
        # 构造请求体 - 支持不同API格式
        if "/chat" in api_url or "chat" in api_url.lower():
            # Chat API 格式
            messages = []
            
            # 如果有对话历史且处于多轮对话模式，则添加历史记录
            if history is not None and len(history) > 0:
                messages.extend(history)
            
            # 添加当前用户消息
            if image_path and os.path.exists(image_path):
                # 添加图像内容到消息中
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_to_base64(image_path)}"}}
                    ]
                })
            else:
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            
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
                return _("api_errors.no_response")
        else:
            return _("api_errors.status_error", code=response.status_code)
            
    except requests.exceptions.Timeout:
        return _("api_errors.timeout")
    except requests.exceptions.ConnectionError:
        return _("api_errors.connection_error")
    except Exception as e:
        return _("api_errors.error_occurred", error=str(e))


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
        return f"Image encoding error: {str(e)}"


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
    print(_("app_title"))
    print(_("app_description"))
    print("=" * 60)
    print("💡 " + _("feature_list.title"))
    print(_("feature_list.real_time_chat"))
    print(_("feature_list.multiple_api"))
    print(_("feature_list.friendly_ui"))
    print(_("feature_list.error_handling"))
    print("=" * 60)


def print_help():
    """打印帮助信息"""
    print(f"\n{_('help_title')}")
    print(_("commands.ask_question"))
    print(_("commands.quit"))
    print(_("commands.clear"))
    print(_("commands.help"))
    print(_("commands.info"))
    print(_("commands.model"))
    print(_("commands.image"))
    print(_("commands.multiturn"))
    print(_("commands.single"))
    print(_("commands.lang_help"))
    print(_("commands.lang_switch"))
    print("=" * 60)


def print_api_info(api_url: str):
    """打印API信息"""
    print(f"\n{_('api_info.title')}")
    print(_("api_info.address", api_url=api_url))
    connection_status = "✅ 可用" if test_api_connection(api_url) else "⚠️  不可用"
    print(_("api_info.status", status=connection_status))


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
        
        log(_("image_server.connecting"))
        log(_("image_server.target", host=host, port=port))
        
        # 创建TCP连接
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(timeout)  # 设置超时
        
        # 连接到服务器
        client_socket.connect((host, port))
        log(_("image_server.connect_success", host=host, port=port))
        
        # 发送"lastimage"命令
        command = "lastimage"
        client_socket.send(command.encode('utf-8'))
        log(_("image_server.sent_command", command=command))
        
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
                log(_("image_server.timeout"))
                break
            except Exception as e:
                log(_("image_server.receive_error", error=str(e)))
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
                    log(_("image_server.timeout"))
                    break
                except Exception as e:
                    log(_("image_server.receive_image_error", error=str(e)))
                    break
        
        log(_("image_server.received_data", size=len(response)))
        
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
                        
                        log(_("image_server.image_saved", path=filepath))
                        log(_("image_server.image_size", size=image_size))
                        
                        # 显示成功信息
                        print(_("messages.image_success"))
                        print(_("messages.file_path", path=filepath))
                        print(_("messages.file_size", size=image_size))
                        print(_("messages.save_time", time=timestamp))
                        
                        # 关闭连接
                        client_socket.close()
                        return filepath
                        
            except ValueError as ve:
                log(_("image_server.image_data_error", error=str(ve)))
            except Exception as e:
                log(_("image_server.process_image_error", error=str(e)))
        
        # 检查是否是错误响应
        elif response.startswith(b"ERROR:"):
            error_msg = response.decode('utf-8')[6:].strip()
            log(_("image_server.server_error", error=error_msg))
            client_socket.close()
            return f"❌ 服务器错误: {error_msg}"
            
        # 检查是否是状态响应
        elif response.startswith(b"STATUS:"):
            status_msg = response.decode('utf-8')[7:].strip()
            log(_("image_server.server_status", status=status_msg))
            client_socket.close()
            return f"📈 服务器状态: {status_msg}"
            
        else:
            # 未知响应格式
            log(_("image_server.unknown_response", response=response[:100]))
            # 尝试显示文本内容
            try:
                text_content = response.decode('utf-8', errors='ignore')
                if text_content.strip():
                    log(_("image_server.text_content", content=text_content[:200]))
            except:
                pass
        
        # 关闭连接
        client_socket.close()
        log(_("image_server.connection_closed"))
        return _("image_server.image_failed")
        
    except socket.timeout:
        log(_("image_server.timeout_error"))
        return _("image_server.timeout_error")
    except ConnectionRefusedError:
        log(_("image_server.refused_error"))
        return _("image_server.refused_error")
    except socket.gaierror as e:
        log(_("image_server.dns_error", error=str(e)))
        return _("image_server.dns_error", error=str(e))
    except Exception as e:
        log(_("image_server.unknown_error", error=str(e)))
        return _("image_server.unknown_error", error=str(e))


def main():
    """主函数：提供交互式对话界面"""
    import sys
    
    # 初始化翻译
    global current_translations, current_language
    
    # 检查命令行参数，支持 --lang 选项
    for i, arg in enumerate(sys.argv):
        if arg in ['--lang', '-l'] and i + 1 < len(sys.argv):
            lang_code = sys.argv[i + 1].lower()
            if lang_code in ['en', 'zh']:
                current_language = lang_code
    
    current_translations = load_translations(current_language)
    
    # 检查是否需要自动显示帮助信息并退出
    if '--help' in sys.argv or '-h' in sys.argv:
        print_header()
        print_help()
        return
    
    print_header()
    
    # 默认API地址
    api_url = "http://localhost:8000/v1/chat/completions"
    model = "qwen3-30b-vl"
    
    # 获取用户输入的API地址（可选）
    print(f"\n{_('messages.config_api')}")
    print(_("messages.default_address", api_url=api_url))
    custom_api = input(_("messages.enter_custom_api")).strip()
    if custom_api:
        api_url = custom_api
    
    # 获取用户输入的模型名称（可选）
    print(_("messages.default_model", model=model))
    custom_model = input(_("messages.enter_custom_model")).strip()
    if custom_model:
        model = custom_model
    
    # 测试连接
    print(_("messages.connecting", api_url=api_url))
    if test_api_connection(api_url):
        print(_("messages.connection_success"))
    else:
        print(_("messages.connection_warning"))
        print(_("messages.connection_advice"))
    
    print("\n" + "-" * 60)
    print(_("messages.start_chat"))
    print("-" * 60)
    
    # 交互式对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input(_("messages.your_question")).strip()
            
            # 处理各种命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(_("messages.goodbye"))
                break
            
            # 处理清除命令
            if user_input.lower() in ['clear', 'cls']:
                print(_("messages.history_cleared"))
                # 清除对话历史
                global conversation_history
                conversation_history = []
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
                new_model = input("   " + _("messages.enter_model") + " ").strip()
                if new_model:
                    model = new_model
                    print(_("messages.model_switched", model=model))
                continue
            
            # 处理语言命令
            if user_input.lower().startswith('lang'):
                parts = user_input.split()
                if len(parts) == 1:
                    # 显示当前语言
                    print(_("messages.current_lang", lang=current_language))
                elif len(parts) == 2:
                    # 切换语言
                    lang_code = parts[1].lower()
                    if lang_code in ['en', 'zh']:
                        switch_language(lang_code)
                    else:
                        print(_("messages.lang_invalid"))
                else:
                    print(_("messages.lang_invalid"))
                continue
            
            # 处理多轮对话模式命令
            if user_input.lower() == 'multiturn':
                print(_("messages.multiturn_mode"))
                print(_("messages.multiturn_info_1"))
                print(_("messages.multiturn_info_2"))
                print(_("messages.multiturn_info_3"))
                print(_("messages.multiturn_info_4"))
                print(_("messages.multiturn_info_5"))
                global is_multiturn_mode
                is_multiturn_mode = True
                continue
            
            # 处理退出多轮对话模式命令
            if user_input.lower() == 'single':
                print(_("messages.single_mode"))
                is_multiturn_mode = False
                # 清除对话历史
                conversation_history = []
                continue
            
            # 处理图像命令
            if user_input.lower() == 'image':
                # 从服务器获取图片
                print(_("messages.getting_image"))
                image_path = get_last_image_from_server()
                print(_("messages.server_response", response=image_path))
                if image_path and image_path.startswith("./images"):
                    print(_("messages.image_obtained", filename=os.path.basename(image_path)))
                    # 明确提示用户输入问题
                    question = input(_("messages.enter_question")).strip()
                    if not question:
                        print(_("messages.question_empty"))
                        continue
                    # 发送带图像和问题的请求
                    print(_("messages.processing"))
                    print(_("messages.please_wait"))
                    # 如果在多轮对话模式下，传递对话历史
                    if is_multiturn_mode:
                        response = get_api_response(question, api_url, model, image_path, conversation_history)
                    else:
                        response = get_api_response(question, api_url, model, image_path)
                    
                    # 如果在多轮对话模式下，更新对话历史
                    if is_multiturn_mode and response != "":
                        # 添加用户消息到历史（包含图片信息）
                        conversation_history.append({
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": question},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_to_base64(image_path)}"}}
                            ]
                        })
                        # 添加AI响应到历史
                        conversation_history.append({"role": "assistant", "content": response})
                else:
                    if "❌" in image_path:
                        print(_("image_server.image_path_warning", image_path=image_path))
                        # 重新提示用户输入其他内容
                        continue
                    # 发送普通请求
                    print(_("messages.processing"))
                    print(_("messages.please_wait"))
                    # 如果在多轮对话模式下，传递对话历史
                    if is_multiturn_mode:
                        response = get_api_response(user_input, api_url, model, None, conversation_history)
                    else:
                        response = get_api_response(user_input, api_url, model)
            else:
                # 处理空输入
                if not user_input:
                    print(_("messages.invalid_question"))
                    continue
                
                # 发送请求并显示响应
                print(_("messages.processing"))
                print(_("messages.please_wait"))
                
                # 如果在多轮对话模式下，传递对话历史
                if is_multiturn_mode:
                    response = get_api_response(user_input, api_url, model, None, conversation_history)
                else:
                    response = get_api_response(user_input, api_url, model)
                
                # 如果在多轮对话模式下，更新对话历史
                if is_multiturn_mode and response != "":
                    # 添加用户消息到历史
                    conversation_history.append({"role": "user", "content": user_input})
                    # 添加AI响应到历史
                    conversation_history.append({"role": "assistant", "content": response})
            
            # 显示响应
            print(_("messages.ai_response"))
            print("-" * 40)
            print(response)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print(_("messages.interrupted"))
            break
        except Exception as e:
            print(_("messages.error_occurred", error=str(e)))
            print(_("messages.retry_advice"))


if __name__ == "__main__":
    main()