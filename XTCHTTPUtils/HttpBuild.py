import requests
from XTCHTTPUtils.Eebbk import Eebbk
from typing import Optional
from .log import Logger


class Http_Build:

    def __init__(self, data: dict) -> None:
        self.data = data
        self.logger = Logger()

    def build(self) -> Optional[requests.Request]:
        try:
            headers = {
                'Base-Request-Param': '{"accountId":"' + self.data['watchid'] + '","appId":"2","deviceId":"' +
                                      self.data['bindnumber'] +
                                      '","imFlag":"1","mac":"unknown","program":"watch","registId":0,'
                                      '"timestamp":"2024-08-01800:15:00","token":"'
                                      + self.data['chipid'] + '"}',
                'imSdkVersion': '102',
                'packageVersion': '52802',
                'dataCenterCode': 'CN_BJ',
                'Version': 'W_1.3.0',
                'Grey': '0',
                'User-Agent': 'okhttp/3.12.0',
                'Content-Type': 'application/json; charset=utf-8',
                'Accept-Encoding': 'gzip',
                'Content-Encoding': 'gzip',
                'Accept-Language': 'zh_CN',
                'Watch-Time-Zone': 'GMT+08:00',
                'model': 'ND07',
                'encrypted': 'encrypted'
            }
            url = self.data['url']
            body = self.data['body']
            return requests.Request(method='POST', url=url, headers=headers, data=body)
        except Exception as e:
            self.logger.error('构建请求时发生错误！请检查参数是否正确！错误见下：' + str(e))
            return None

    def send(self, request: requests.Request, key: str) -> Optional[dict]:
        try:
            session = requests.Session()
            response = session.send(request.prepare(), proxies={})
            decrypted_data_dict = Eebbk.eebbkDecrypt(response, key)
            return decrypted_data_dict
        except Exception as e:
            self.logger.error('请求时发生了一个错误，错误见下：' + str(e))
            return None
