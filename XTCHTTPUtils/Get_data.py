import sys
import json
import os
from typing import Optional
from . import log


# 生成文件方法
def create_data_file() -> None:
    """创建文件"""
    data = {
        "bindnumber": "",
        "chipid": "",
        "rsaKey": "",
        "KeyId": "",
        "model": "",
        "watchid": ""
    }
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)


class Get_data:

    def __init__(self):
        self.data = None
        self.logger = log.Logger()

    def load_input(self) -> Optional[dict]:
        try:
            url = input("请输入你要请求api的url网址：")
            body = input("请输入你请求api的body（输入 JSON 格式的字符串）：")

            return {"url": url, "body": body}
        except KeyboardInterrupt:
            self.logger.error('\n正在停止脚本...')
            sys.exit(0)  # 正常退出程序

    def file_disp(self, file_path='data.json') -> Optional[dict]:
        """**重要提示**：\n
        ! 调用此对象时，请先调用我！\n
        返回：
            字典或None (dict | None)
            
        """

        if not os.path.exists(file_path):
            # 如果文件不存在，则创建并写入初始数据
            create_data_file()
            self.logger.warn('data.json 文件已创建，请补全文件内容后再启动程序！')
            sys.exit(0)  # 提示用户补全文件后再启动程序

        # 文件存在时，检查是否为空或有无效内容
        try:
            with open("data.json", "r", encoding='utf-8') as file:
                content = file.read().strip()  # 去掉前后空白字符
                if not content:  # 若文件内容为空，提示用户补全
                    create_data_file()
                    self.logger.error("data.json 文件为空，请补全文件内容后再启动程序！")
                    sys.exit(1)
                # 将内容加载为 JSON 数据
                self.data = json.loads(content)

        # 如果发生错误，就删除文件，然后重新生成文件
        except json.JSONDecodeError:
            self.logger.error("data.json 文件内容无效，请检查 JSON 格式！已重新生成文件！")
            os.remove(file_path)  # 删除文件
            create_data_file()  #
            sys.exit(1)

        except ValueError as e:
            os.remove(file_path)
            create_data_file()
            self.logger.error(f'读取配置文件时出现了一个错误，已重新生成配置文件。错误见下：{e}')
            sys.exit(1)
        if not self.data:
            return None

        required_keys = ['watchid', 'bindnumber', 'chipid', 'KeyId', 'rsaKey']
        if not all(key in self.data for key in required_keys):
            os.remove(file_path)
            create_data_file()
            self.logger.error('配置文件错误！已重新生成！')
            sys.exit(1)

        for key in self.data:
            if not self.data[key]:
                self.logger.warn('请补全配置文件后再运行此软件！！！')
                sys.exit(1)

        self.data.update(self.load_input())
        return self.data
