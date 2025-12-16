import subprocess
import json
import tomllib
from datetime import datetime

class Default:

    class config:
        py_text = ""
        py_file = "config.py"
        toml_file = "config.toml"

    class requests:
        headers = {
            "Accept": "application/json"
            }

    class project:

        path = {
            "template": "template.json",
            "configs": "configs",
            "test": "test.json",
            "source": "source",
            "binary": "binary"
            }
        
    class log:
        level_str_to_int = {"error": 0, "warn": 1, "info": 2, "debug": 3 }
        level_str = "debug"

def process_script(cmd:list):

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
            encoding='utf-8',errors='ignore')
        
        if result.returncode == 0:
            print(f"命令执行成功 {result.stdout}")
        else: raise Exception(result.stderr)
        return True
    except Exception as e:
        print(f"命令执行失败，检查输入{e}")
        return False 
    
class Log:

    def __init__(self):
        config_toml = File.Read(Default.config.toml_file).toml()
        try:
            log_config = config_toml['Log']
            level_config_str = log_config['level']
        except KeyError as e:
            print(f"{datetime.now()} [WARN] 由于{e}, 日志默认为 info。") 
            level_config_str = Default.log.level_str

        self.level_to_int = Default.log.level_str_to_int
        self.level_config_int = self.level_to_int[level_config_str]
        print(f"{datetime.now()} [INFO] 输出日志等级为 {level_config_str}")
        
        try:
            self.path = log_config['path']
            print(f"{datetime.now()} [INFO] 日志路径为 {self.path}")
        except Exception as e:
            print(f"{datetime.now()} [INFO] 没有设定日志路径，不写入日志文件。") 
            self.path = False

    def main(self, level_str:str, data:str):
        """
        main 的 Docstring
        
        :param level_str: 日志等级， level debug warn error
        :param data: 日志内容，字符串
        return None
        outpath: {当前时间 + 大写日志等级 + 日志内容}
        """

        # 判断输出日志类型， 当配置的日志等级大于等于打印等级时，输出日志
        def is_output():
            level_int = self.level_to_int[level_str]
            return True if self.level_config_int >= level_int else False

        # 打印日志
        def printf(): print(self.content)

        # 将日志写入文件
        def write():
            File.write(self.path).common(self.content, mode='a')

        now = datetime.now()
        self.content = f"{now} [{level_str.upper()}] {data}\r"

        if not is_output(): return
        
        if self.path: write()
        else: printf()
            

    def info(self, data):
        self.main(self.info.__name__, data)

    def debug(self, data):
        self.main(self.debug.__name__, data)

    def warn(self, data):
        self.main(self.warn.__name__, data)

    def error(self, data):
        self.main(self.error.__name__, data)
    
class File:
    """
    文件的读取和写入函数
    写入 json write_json
    读取文件 read_file
    """

    class write:

        def __init__(self, path):
            self.path = path

        def common(self, data, mode='w'):
            """内部函数， 将数据写入到文件中
            param: 
                path: 文件写入文件路径
                config: 写入的数据
            return: None"""
            with open(self.path, mode, encoding='utf-8') as f: f.write(data)

        def binary(self, data):
            with open(self.path, 'wb', encoding='utf-8') as f: f.write(data)

        def json(self, data):
            # 将 json 类型的数据保存为文件
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    class Read:
        
        def __init__(self, path):
            self.path = path

        def main(self, mode='r', encoding='utf-8', type="common"):
            with open(self.path, mode, encoding=encoding) as f: 
                if type == "common":
                    content = f.read()
                elif type == "json":
                    content = json.load(f)
                elif type == "toml":
                    content = tomllib.load(f)
                return content

        def common(self):
            # 读取文件
            return self.main()

        def json(self):
            return self.main(type="json")

        def toml(self):
            return self.main(mode='rb', type='toml', encoding=None)