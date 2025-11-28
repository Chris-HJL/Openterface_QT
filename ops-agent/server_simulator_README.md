# Openterface 服务端模拟器使用说明

## 功能概述

Openterface 服务端模拟器是一个用于测试和开发的工具，模拟 Openterface 项目中的 TCP 服务器功能，并提供 HTTP 接口用于动态管理图片路径。

### 主要特性

- **TCP 服务器**：模拟原始服务器，处理 `lastimage` 命令
- **HTTP 接口**：支持通过 curl 命令查询和更新图片路径
- **动态配置**：无需重启服务器即可更改图片文件
- **多线程处理**：支持多个客户端同时连接

## 快速开始

### 启动服务器

```bash
python server_simulator.py
```

服务器启动后，会同时运行两个服务：

- **TCP 服务器**：`localhost:12345`
- **HTTP 服务器**：`localhost:8080`

### 默认配置

- 初始图片路径：`C:\Users\huang\Pictures\openterface\1.jpg`
- TCP 端口：12345
- HTTP 端口：8080

## 使用说明

### 1. TCP 服务器使用

TCP 服务器用于处理 `lastimage` 命令，返回指定的图片数据。

**客户端连接示例：**

```python
import socket

# 连接到服务器
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 12345))

# 发送命令
client.send(b'lastimage\n')

# 接收响应
response = client.recv(1024)
print(response.decode())

# 接收图片数据（根据协议实现）
# ...

client.close()
```

### 2. HTTP 接口使用

HTTP 服务器提供 RESTful API 用于管理图片路径。

#### 查询当前图片路径

```bash
curl http://localhost:8080/image-path
```

**返回示例：**

```json
{
    "status": "success",
    "image_path": "C:\\Users\\huang\\Pictures\\openterface\\1.jpg",
    "exists": true
}
```

#### 更新图片路径

服务器支持多种数据格式来更新图片路径：

**格式 1：直接格式（推荐）**
```bash
curl -d 'path=C:\Users\huang\Pictures\openterface\2.jpg' http://localhost:8080/image-path
```

**格式 2：URL 编码格式**
```bash
curl -d "path=C%3A%5CUsers%5Chuang%5CPictures%5Copenterface%5C2.jpg" http://localhost:8080/image-path
```

**格式 3：JSON 格式**
```bash
curl -d '{"path": "C:\\Users\\huang\\Pictures\\openterface\\2.jpg"}' http://localhost:8080/image-path
```

**参数说明：**

- `path`：新的图片文件完整路径（必需）
- 服务器会自动尝试三种不同的解析方式来获取路径参数

**返回示例：**

```json
{
    "status": "success",
    "message": "图片路径已更新为: C:\\path\\to\\new\\image.jpg",
    "path": "C:\\path\\to\\new\\image.jpg"
}
```

#### 错误处理

如果请求缺少必要的参数或发生错误，服务器会返回相应的错误信息：

```json
{
    "status": "error",
    "message": "缺少path参数"
}
```

## 实际应用场景

### 场景 1：自动化测试

在自动化测试脚本中动态切换测试图片：

```bash
#!/bin/bash

# 启动服务器（在后台）
python server_simulator.py &
SERVER_PID=$!

# 等待服务器启动
sleep 2

# 测试图片1
curl -d "path=C:\\test\\image1.jpg" http://localhost:8080/image-path
# 执行测试...

# 测试图片2
curl -d "path=C:\\test\\image2.jpg" http://localhost:8080/image-path
# 执行测试...

# 清理
kill $SERVER_PID
```

### 场景 2：开发调试

在开发过程中快速切换不同的测试图片：

```bash
# 查看当前图片
curl http://localhost:8080/image-path

# 切换到调试图片
curl -d "path=C:\\dev\\debug\\sample.png" http://localhost:8080/image-path

# 切换回默认图片
curl -d "path=C:\\Users\\huang\\Pictures\\openterface\\1.jpg" http://localhost:8080/image-path
```

## 注意事项

1. **路径格式**：支持多种路径格式
   - 直接格式：`C:\Users\test\image.jpg`（推荐，无需转义）
   - 双反斜杠：`C:\\Users\\test\\image.jpg`
   - 正斜杠：`C:/Users/test/image.jpg`
   - URL 编码：`C%3A%5CUsers%5Ctest%5Cimage.jpg`

2. **字符编码**：服务器返回的 JSON 响应现在支持 UTF-8 编码，中文字符会正常显示而不是 Unicode 转义序列

2. **文件存在检查**：HTTP 接口会检查文件是否存在，但 TCP 服务器在发送图片时会进行实际的读取操作

3. **线程安全**：使用锁机制确保多线程环境下的路径更新安全

4. **错误处理**：如果指定的图片文件不存在或无法读取，TCP 服务器会返回错误信息

5. **端口占用**：确保端口 12345 和 8080 未被其他程序占用

## 故障排除

### 问题 1：端口被占用

**症状**：启动时提示 "Address already in use"

**解决方案**：
- 检查占用端口的进程：`netstat -ano | findstr :12345`
- 终止占用进程或修改服务器端口

### 问题 2：图片文件无法读取

**症状**：客户端收到 "ERROR: 图片文件不存在" 或 "无法读取图片文件"

**解决方案**：
- 使用 HTTP 接口查询当前路径：`curl http://localhost:8080/image-path`
- 检查路径是否正确
- 确认文件存在且有读取权限

### 问题 3：curl 命令返回 404

**症状**：`curl: (22) The requested URL returned error: 404`

**解决方案**：
- 确认 URL 路径正确：`/image-path`
- 确认 HTTP 服务器已启动（查看控制台输出）
- 检查端口是否正确：8080

## 高级用法

### 修改默认端口

编辑 `server_simulator.py` 文件，修改以下变量：

```python
TCP_PORT = 12345  # TCP 服务器端口
HTTP_PORT = 8080  # HTTP 服务器端口
```

### 修改默认图片路径

编辑 `server_simulator.py` 文件，修改全局变量：

```python
current_image_path = r"C:\Your\Default\Path\image.jpg"
```

## 技术细节

### 通信协议

#### TCP 协议

1. 客户端发送命令：`lastimage\n`
2. 服务器响应格式：
   - 成功：`IMAGE:{size}\n` + 二进制图片数据
   - 失败：`ERROR: {message}\n`

#### HTTP 协议

- **查询路径**：`GET /image-path`
- **更新路径**：`POST /image-path` 
  - 支持多种数据格式：application/x-www-form-urlencoded、纯文本、JSON
  - 字符编码：UTF-8，确保中文字符正常显示

### 数据结构

```python
# 全局变量
current_image_path    # 当前图片路径（字符串）
image_path_lock       # 线程锁（threading.Lock）
```

## 许可证

本项目基于 Openterface Mini-KVM 项目的许可证。

## 支持与反馈

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 联系开发团队

---

**版本**：1.0.0  
**最后更新**：2025年11月28日
