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
   - **设备配置**：在左侧填写 `watchid`、`bindnumber`、`chipid`、`rsaKey`、`KeyId`、`model` 后点击「保存配置」（写入 `data.json`，下次启动自动加载，`model` 可选）。
   - **编辑请求**：在右侧输入 API 地址和 JSON body，支持一键格式化，再点击「发送请求」。
   - **响应结果**：切换 **JSON / 表格 / 日志**，可复制当前页内容；日志页支持清空日志。
   - **状态提示**：顶部显示发送状态，响应区显示耗时与返回码；输入错误会在请求区提示。
   - **快捷键**：`Ctrl+Enter` 发送、`Ctrl+S` 保存配置（macOS 使用 `⌘`）；请求与响应区之间可拖动调整高度，小窗口下支持滚动。
