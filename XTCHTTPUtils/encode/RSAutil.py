from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
from typing import Optional
from XTCHTTPUtils.log import Logger


class RSAUtil:

    @staticmethod
    def encrypt(data: str, public_key: str) -> Optional[str]:
        logger = Logger()
        try:
            public_key_obj = RSA.import_key(base64.b64decode(public_key))  # 公钥对象
            cipher = PKCS1_v1_5.new(public_key_obj)  # 使用公钥进行加密
            encrypted_data = cipher.encrypt(data.encode('utf-8'))  # 加密数据
            return base64.b64encode(encrypted_data).decode('utf-8')  # 返回 base64 编码的加密数据
        except Exception as e:
            logger.error(f'加密数据失败！请检查公钥是否正确！错误信息：{e}')
            return None

    @staticmethod
    def decrypt(data: str, private_key: str) -> Optional[str]:
        logger = Logger()
        try:
            private_key_obj = RSA.import_key(base64.b64decode(private_key))  # 私钥对象
            cipher = PKCS1_v1_5.new(private_key_obj)  # 使用私钥进行解密
            encrypted_data = base64.b64decode(data)  # 解码输入的 base64 编码数据
            decrypted_data = cipher.decrypt(encrypted_data, None).decode('utf-8')  # 解密数据并转换为字符串
            return decrypted_data
        except Exception as e:
            logger.error(f'解密数据失败！请检查私钥是否正确！错误信息：{e}')
            return None
