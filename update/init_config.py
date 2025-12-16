from pathlib import Path
import update

Default = update.Default
File = update.File
log = update.Log()

config_text = Default.config.py_text
config_content = File.Read(Default.config.toml_file).toml()
py_config = Default.config.py_file
project_path_list = Default.project.path

def splicing_config_content(content:str, is_empty=True, indent=4):
    global config_text
    empty = " " if is_empty else ""
    empty = empty * indent
    config_text += f"{empty}{content}\n"

def inspect_root(class_content):

    try:
        root = class_content['root']
    except KeyError:
        root = './'
        log.debug("没有指定根目录地址，使用默认根目录%s"%Path(root))
    return Path(root)

def generate_project_config(root:Path):
    """生成 project 类的配置项"""

    def create_folder(dir:Path):

        if not dir.exists():
            if Path(dir).suffix:
                log.debug("%s 是文件，停止创建文件夹"%dir); return
            try:
                Path(dir).mkdir(parents=True, exist_ok=True)
                log.debug(f"创建目录{dir}")
            except PermissionError:
                log.error("创建根目录时权限不足，请检查并重试")
    splicing_config_content("class Project:", is_empty=False)
    for path_map in project_path_list:
        full_path = root.joinpath(project_path_list[path_map])
        create_folder(full_path)
        splicing_config_content(f"{path_map} = r'{full_path}'")

def generate_requests_config(requests_content:dict):
    """
    generate_requests_config 的 Docstring
    将配置项写入到 config.py 文件中
    class requests:
        headers = {}
        class url:
            __generate_group_url()

    :param requests_content: dict
        requests_content: {
            "header": "Accept": "application/json",
            "url": {
                "site-miceosoft": [
                    "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-microsoft.srs"
                ],
                "site-github": [
                	"https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-github.srs"
                ] 
            },
        }
    :return None
    """
    def __generate_group_url(greoup_url_list:dict):
        """
        __generate_group_url 的 Docstring
        将配置写入到配置文件中 config.py
        class url:
            site_microsoft = [a_url, b_url]
            site_microsoft_cn = [c_url]
        
        :param greoup_url_list: dict
        url = {
            "site-microsoft" : [a_url, b_url],
            "site-microsoft-cn" : [c_url] 
        }
        :return None
        """
        splicing_config_content("class url:", indent=4)
        for group_name in greoup_url_list:
            url_list = greoup_url_list[group_name]
            group_name = group_name.replace("-", "_")
            splicing_config_content(f"{group_name} = {url_list}", indent=8)
        
    
    if not requests_content: 
        log.warn("配置项 requests 没有内容， 停止生成 requests 类"); return
    splicing_config_content("class Requests:", is_empty=False)
    
    # 生成 requests 配置 
    for key in requests_content:
        # 生成 url 配置
        if key == 'url':
            greoup_url_list = requests_content[key]
            __generate_group_url(greoup_url_list)
        # 生成 header 配置
        elif key == "headers":
            headers = requests_content[key]
            splicing_config_content(f"{key} = {headers}")
        
def generate_proxy_config(proxy_content):
    
    try:
        flag = proxy_content['flag']
        url = proxy_content['url']
        port =proxy_content['port']
    except KeyError:
        return 

    if not flag: return

    splicing_config_content("class Proxy:", is_empty=False)

    url = "'http://%s:%s'" % (url, port)
    content = '''import os
    os.environ["HTTP_PROXY"] = {0}
    os.environ["HTTPS_PROXY"] = {0}
    os.environ["http_proxy"] = {0}
    os.environ["https_proxy"] = {0}\n'''.format(url)
    splicing_config_content(content)


def generate_program_config(program_content):

    if not program_content: return
    splicing_config_content("class Program:", is_empty=False)
    for param in program_content:
        param_path = program_content[param]
        param = param.replace('-', '_')
        splicing_config_content(f"{param} = '{param_path}'")


log.info("初始化 update sing-box config 配置文件")
for name in config_content:
    class_content = config_content[name]
    ## 生成 Project:
    if name.lower() == "project":
        root = inspect_root(class_content)
        generate_project_config(root)
        log.debug("生成配置 project") 

    if name.lower() == 'requests': 
        generate_requests_config(class_content)
        log.debug("生成配置 requests") 
        
    if name.lower() == 'porxy': 
        generate_proxy_config(class_content)
        log.debug("生成配置 porxy")

    if name.lower() == 'program':
        generate_program_config(class_content)
        log.debug("生成配置 Program")

File.write(py_config).common(config_text)