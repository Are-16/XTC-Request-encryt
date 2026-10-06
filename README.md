# XTC-Request-encrypt[![Build and Release](https://github.com/Are-16/XTC-Request-encryt/actions/workflows/pack.yaml/badge.svg)](https://github.com/Are-16/XTC-Request-encryt/actions/workflows/pack.yaml)

## 适用于小天才请求加密的仓库

### 系统要求：
- Python 3.9 或更高版本

## 使用方法：

### 方法一：下载可执行文件
1. 下载 `Releases` 中与你系统匹配的可执行二进制文件。

### 方法二：从源码运行(建议使用，可以安装最新版本)
1. 克隆仓库：
   ```bash
   git clone https://github.com/Are-16/XTC-Request-encrypt.git
   ```
2. 进入仓库目录：
   ```bash
   cd XTC-Request-encrypt
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 运行程序：
   
   - 默认启动图形界面（GUI）：
   
     - **Linux/macOS**：
       ```bash
       python3 main.py
       ```
     - **Windows**：
       ```bash
       python main.py
       ``` 
   
   - 如需使用命令行模式（原交互流程）：
     ```bash
     python main.py --cli
     ``` 
   
   GUI 界面说明：
   - **设备配置**：填写 `watchid`、`bindnumber`、`chipid`、`rsaKey`、`KeyId`、`model` 后点击「保存配置」（写入 `data.json`，下次启动自动加载）。
   - **请求**：输入要请求的 API 的 URL 和 JSON 格式的 body，点击「发送请求」。
   - **响应 JSON / 响应 表格**：查看解密后的响应；**日志**：查看运行日志。
