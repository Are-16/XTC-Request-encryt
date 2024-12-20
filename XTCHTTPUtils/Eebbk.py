import requests
from XTCHTTPUtils.encode.AESkey import AESencode
from XTCHTTPUtils.encode.MD5 import MD5Util
from XTCHTTPUtils.encode.RSAutil import RSAUtil
import io
import gzip
from typing import Optional
from XTCHTTPUtils.log import Logger
import json

# 日志配置

class Eebbk:
    """一个小天才加密的类\n
    含小天才加密方法"""

    @staticmethod
    def generate_sign(key: str, url: str, param: str, bArr: bytes) -> Optional[str]:
        logger = Logger()
        byte_array_output_stream = io.BytesIO()
        try:
            byte_array_output_stream.write(url.encode('utf-8'))
            byte_array_output_stream.write(param.encode('utf-8'))
            if bArr:
                byte_array_output_stream.write(bArr)
            byte_array_output_stream.write(key.encode('utf-8'))
            combined_bytes = byte_array_output_stream.getvalue()
            return MD5Util.encode(combined_bytes)
        except Exception as e:
            logger.error(f'创建签名时失败！原因：{e}')
            return None

    @staticmethod
    def eebbk_Encrypt(request: requests.Request, key: str, publickey: str, keyId: str) -> Optional[requests.Request]:
        """加密小天才api的请求\n
        输入：
            request (requests.Request)
            AESkey (str)
            RSA public key (str)
            KeyId (str)
        样例输入：
        ```python
        from utils.Eebbk import Eebbk
        import requests
        request = ...
        key = ...
        rsakey = ...
        keyid = ...
        request = Eebbk.eebbkEncrypt(request, key, rsakey, keyid)
        
    ```
        输出：
            加密后的请求对象 (requests.Request)
"""
        logger = Logger()
        # 获取和解码初始body
        origbody = request.data or ""
        if isinstance(origbody, bytes):
            origbody = origbody.decode('utf-8')

        # 获取初始参数并生成签名
        origparam = request.headers.get('Base-Request-Param')
        sign = Eebbk.generate_sign(key, request.url, origparam or "", origbody.encode('utf-8'))

        # 加密和设置 Base-Request-Param 参数
        if origparam:
            encryptedParam = AESencode.encode(origparam, key)
            if encryptedParam:
                request.headers['Base-Request-Param'] = encryptedParam
            else:
                logger.error('加密Base-Request-Param失败！')
        # 设置签名和其他header
        if sign:
            request.headers['Eebbk-Sign'] = sign
        
        request.headers['Eebbk-Key-Id'] = keyId
        eERsa_Key = RSAUtil.encrypt(key, publickey)
        if eERsa_Key:
            request.headers['Eebbk-Key'] = eERsa_Key
        else:
            return None
        request.headers['Content-Encoding'] = 'gzip'
        request.headers['encrypted'] = 'encrypted'

        try:
            # 压缩并加密请求体
            if origbody:
                compressed_body = gzip.compress(origbody.encode('utf-8'))
                encrypted_body = AESencode.encode_bytes(compressed_body, key)
                if encrypted_body:
                    request.data = encrypted_body
                else:
                    logger.error('加密body失败！')
                    return None
        except Exception as e:
            logger.error(f"处理body时发生错误！报错信息：{e}")
            return None

        return request

    @staticmethod
    def eebbkDecrypt(response: requests.Response, key: str) -> dict:
        """解密小天才返回的响应
        输入：response (requests.Response)
            AESkey (str)
        返回：解密后的状态码和具体body，dict格式。两个字段：code,body
        """
        decrypted_body = response.text[1:-1]
        if decrypted_body:
            decrypted_body = AESencode.decrypt_response(decrypted_body, key)
        xtc_response_dict = {'code': json.loads(decrypted_body).get('code'),
                    'body':decrypted_body}
        return xtc_response_dict
