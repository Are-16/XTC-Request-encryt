from urllib.parse import urlparse

def extract_second_level_and_top_level_domain(url):
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
            return second_level, top_level
        else:
            return None, None
    else:
        return None, None

# 测试样例
urls = [
    "https://www.baidu.com",        # https://www.baidu.com
    "http://api.okii.com",         # http://api.okil.com
    "https://ftp.example.org",     # https://ftp.example.org
    "ftp://www.example.co.uk",     # ftp://www.example.co.uk
    "http://www.subdomain.example.com",  # 多级子域名
    "www.example.com",             # www.example.com（没有协议）
]

for url in urls:
    second_level, top_level = extract_second_level_and_top_level_domain(url)
    if second_level and top_level:
        print(f"URL: {url}\n二级域名: {second_level}\n一级域名: {top_level}\n")
    else:
        print(f"URL: {url}\n无法提取二级和一级域名\n")
