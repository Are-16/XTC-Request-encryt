import base64
import gzip
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESencode:
    @staticmethod
    def _get_cipher(key: str, mode) -> AES:
        """创建 AES cipher 对象"""
    # 使用 AES 的模式常量而不是普通的 int
        return AES.new(key.encode('utf-8'), mode)

    @staticmethod
    def encode(text: str, key: str) -> Optional[str]:
        """加密字符串并返回 base64 编码的加密字符串"""
        try:
            cipher = AESencode._get_cipher(key, AES.MODE_ECB)
            encrypted_data = cipher.encrypt(pad(text.encode('utf-8'), AES.block_size))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            print(f'AES加密失败！原因: {e}')
            return None

    @staticmethod
    def encode_bytes(text: bytes, key: str) -> Optional[str]:
        """加密字节数据并返回 base64 编码的加密字符串"""
        try:
            cipher = AESencode._get_cipher(key, AES.MODE_ECB)
            encrypted_data = cipher.encrypt(pad(text, AES.block_size))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            print(f'AES加密失败！原因: {e}')
            return None

    @staticmethod
    def decrypt_response(encrypted_text: str, key: str) -> Optional[str]:
        """解密 base64 编码的加密字符串并返回明文"""
        try:
            encrypted_data = base64.b64decode(encrypted_text)
            cipher = AESencode._get_cipher(key, AES.MODE_ECB)
            decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            decompressed_data = gzip.decompress(decrypted_data).decode('utf-8')
            return decompressed_data
        except Exception as e:
            print(f'AES解密失败！！！原因: {e}')
            return None
