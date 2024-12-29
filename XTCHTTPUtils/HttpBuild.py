import requests
from XTCHTTPUtils.Eebbk import Eebbk
from typing import Optional
from .log import Logger
from urllib.parse import urlparse

class Http_Build:

    def __init__(self, data: dict) -> None:
        self.data = data
        self.logger = Logger()
    def extract_second_level_and_top_level_domain(self,url):
        # 解析 URL 获取主机部分
        parsed_url = urlparse(url)
        host = parsed_url.hostname  # 获取主机名（不包含协议和端口）

        if host:
            # 拆分主机名
            parts = host.split('.')  # 按 '.' 拆分域名部分
            if len(parts) >= 2:
                # 获取二级域名和一级域名
                second_level = parts[-2]  # 倒数第二部分是二级域名
                top_level = parts[-1]  # 最后一部分是一级域名
                domain = f'{second_level}.{top_level}'
                return domain
            else:
                return None
        else:
            return None
        
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
            if url:
                domain = self.extract_second_level_and_top_level_domain(url)
                if domain:
                    if domain != 'okii.com':
                        self.logger.error('你确定是小天才域名？？？？')
                        return None
                else:
                    self.logger.error('URL错误！请检查URL是否正确！')
                    return None

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
