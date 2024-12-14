from colorama import Fore, init
import datetime

init(autoreset=True)


class Logger:

    def __init__(self) -> None:
        self.datefmt = '%Y-%m-%d %H:%M:%S'

    def info(self, message: str) -> None:
        var_0 = datetime.datetime.now().strftime(self.datefmt)
        print(f'{var_0} {Fore.GREEN}INFO - {message}')

    def warn(self, message: str) -> None:
        var_1 = datetime.datetime.now().strftime(self.datefmt)
        print(f'{var_1} {Fore.YELLOW}WARNING - {message}')

    def error(self, message: str) -> None:
        var_1 = datetime.datetime.now().strftime(self.datefmt)
        print(f'{var_1} {Fore.RED}ERROR - {message}')
