import XTCHTTPUtils
import uuid
import sys
from tabulate import tabulate

# 将body的键值对转换为表格格式
def display_body_as_table(body: dict) -> str:
    table = [[key, value if value is not None else "null"] for key, value in body.items()]
    return tabulate(table, headers=["字段", "值"], tablefmt="fancy_grid", stralign="center")

# 显示响应信息的函数
def show_info(response_body: dict) -> None:
    if response_body.get('code') != '000001':
        XTCHTTPUtils.logger.warn(f"状态码：{response_body.get('code')}, API返回结果异常")
    
    XTCHTTPUtils.logger.info(f"完整body(JSON形式)：\n{response_body.get('body')}")
    XTCHTTPUtils.logger.info(f"完整body(表格形式)：\n{display_body_as_table(response_body.get('body'))}")

# 生成AES密钥的函数
def generate_aes_key() -> str:
    try:
        key = str(uuid.uuid4()).replace("-", "")[:16]
        if len(key) != 16:
            raise ValueError("生成请求必须的AESkey失败！")
        return key
    except Exception as e:
        XTCHTTPUtils.logger.error(f"生成请求必须的AESkey失败！错误信息：{e}")
        sys.exit(-1)

# 获取请求数据的函数
def get_request_data() -> dict:
    data = XTCHTTPUtils.get_data.file_disp()
    if not data:
        XTCHTTPUtils.logger.error("未获取到有效的请求数据！")
        sys.exit(-1)
    return data

# 请求函数
def b_and_s_request(data: dict,key: str,rsakey: str,keyid: str):
    http_build = XTCHTTPUtils.Http_Build(data)
    request = http_build.build()
    if not request:
        XTCHTTPUtils.logger.error("请求构建失败！")
        sys.exit(-1)
    try:
        encrypted_request = XTCHTTPUtils.Eebbk.eebbk_Encrypt(request, key, rsakey, keyid)
        if not encrypted_request:
            XTCHTTPUtils.logger.error("加密请求失败！")
            sys.exit(-1)
        response_body = http_build.send(encrypted_request, key)
        return response_body
    
    except Exception as e:
        XTCHTTPUtils.logger.error(f"加密或发送请求时发生错误！错误信息：{e}")
        sys.exit(-1)
    
# 主函数
def start() -> None:
    # 获取数据
    data = get_request_data()

    # 获取KeyId和rsakey
    keyid = data['KeyId']
    rsakey = data['rsaKey']

    # 生成AESkey
    key = generate_aes_key()

    # 发送请求
    response_body = b_and_s_request(data,key,rsakey,keyid)

    if not response_body:
        XTCHTTPUtils.logger.error("发送请求失败！")
        sys.exit(-1)

    # 显示信息
    show_info(response_body)
