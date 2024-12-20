import XTCHTTPUtils
import uuid
import sys


def start():
    # 获取数据
    data = XTCHTTPUtils.get_data.file_disp()

    # 使用 Http_build 类构建请求
    http_build = XTCHTTPUtils.Http_Build(data=data)
    request = http_build.build()

    # 获取一些数据
    keyid = data['KeyId']
    rsakey = data['rsaKey']

    # 尝试生成AESkey
    try:
        key = str(uuid.uuid4()).replace("-", "")[:16]
        if len(key) != 16:
            XTCHTTPUtils.logger.error('生成请求必须的AESkey失败！')
            sys.exit(-1)
    except Exception as e:
        XTCHTTPUtils.logger.error(f"生成请求必须的AESkey失败！错误信息：{e}")
        sys.exit(-1)
    # 加密并发送请求
    try:
        request = XTCHTTPUtils.Eebbk.eebbk_Encrypt(request, key, rsakey, keyid)
        
        if not request:
            sys.exit(-1)
        response_body = http_build.send(request, key)
    except Exception as e:
        XTCHTTPUtils.logger.error(f'加密或发生请求失败！错误见下：{e}')

    if not response_body:
        XTCHTTPUtils.logger.error('发送请求失败！')
        sys.exit(-1)
    XTCHTTPUtils.logger.info(f"完整body：{response_body['body']}\n\n")
    XTCHTTPUtils.logger.info(f'状态码：{response_body["code"]}')