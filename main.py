import XTCHTTPUtils
import os
import psutil
import time
import sys
import XTCHTTP_main.XTChttp as XTChttp
import platform

def generate_start_file(parent_name_fun, file_path='xtc.bat'):
    data = f"""set RUN_FROM_BATCH=true
start cmd /K {parent_name_fun}"""

    # 写入批处理文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(data)


def run_cli():
    # 获取当前进程的父进程信息
    parent_process = psutil.Process(os.getppid())
    parent_name = parent_process.name().lower()

    if platform.system() == "Windows":
        if not os.getenv("RUN_FROM_BATCH") and parent_name not in ["cmd.exe", "powershell.exe"]:
            generate_start_file(parent_name)
            XTCHTTPUtils.logger.warn(
                '请勿通过双击直接运行本程序，可能导致一些非预料的后果。已生成安全启动脚本，请点击xtc.bat文件运行')
            time.sleep(3)
            sys.exit(0)

    XTCHTTPUtils.logger.info('程序启动！')

    # 启动程序！
    XTChttp.start()


if __name__ == '__main__':
    if '--cli' in sys.argv:
        # 命令行模式（保留原有交互流程）
        run_cli()
    else:
        # 默认启动图形界面
        from XTCHTTP_main import GUI
        GUI.start()
