import hashlib


class MD5Util:

    @staticmethod
    def encode(input_string) -> str:
        if isinstance(input_string, bytes):
            return MD5Util.encode_bytes(input_string)
        elif isinstance(input_string, str):
            return MD5Util.encode_bytes(input_string.encode('utf-8'))
        else:
            raise TypeError('input_string must be bytes or str')

    @staticmethod
    def encode_bytes(byte_string: bytes) -> str:

        return hashlib.md5(byte_string).hexdigest().upper()
