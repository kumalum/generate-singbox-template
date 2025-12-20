import json
from copy import deepcopy
from singbox import config
from singbox import enum

def readJSON(path=""): 
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def writeJSON(data, path=""):

    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=4, indent=4)


def new_sing_box():
    inline_config = config.FilePath.outinline
    if inline_config.exists():
        return readJSON(inline_config)
    exit("错误：rule_set 设置失败")

def new_sing_box_tag(content):
    ele = enum.Element
    return [rule[ele.tag] for rule in content[ele.route][ele.rule_set]]

def set_inline(conf_route):
    """生成 route.rule_set """
    inline = conf_route[enum.Element.rule_set][enum.Element.inline]

    def __get_dir(suffix='json'):
        root = config.FilePath.root
        suffix = ".%s"%suffix
        return [f for f in root.iterdir() if f.is_file() and f.suffix == suffix]

    config_path = config.FilePath.template

    if not config_path.exists():
        exit("错误：检查模板文件: %s"%config_path)

    rules = []
    config_data = readJSON(config_path)
    for source_file in __get_dir():
        inline = deepcopy(inline)
        data = readJSON(source_file)
        inline[enum.Element.tag] = source_file.with_name(f"site-{source_file.name}").stem.replace("_", "-")
        inline[enum.Element.rules] = data[enum.Element.rules]
        rules.append(inline)

    """将 adguard 以外链的方式加入到 inline 中去"""
    element = enum.Element
    pref_remote = conf_route[element.rule_set][element.remote]
    remote = deepcopy(pref_remote)
    remote[element.tag] = enum.Github.adguard
    remote[element.url] = config.Github.adguard
    rules.append(remote)

    config_data[enum.Element.route][enum.Element.rule_set] = rules
    
    if not config.FilePath.output.exists():
        config.FilePath.output.mkdir(parents=True, exist_ok=True)

    writeJSON(config_data, config.FilePath.outinline)

def group_sing_box_tag(content):

    mode = enum.Mode
    tags = new_sing_box_tag(content)
    direct = {tag for tag in tags if "-cn" in tag}
    block = {tag for tag in tags if "ad" in tag}
    proxy = set(tags) - direct - block

    return {
        mode.proxy: list(proxy),
        mode.direct: list(direct),
        mode.block: list(block)
        }

class UpdateRules:

    def __init__(self, content, element):
        self.content = content
        self.element = element

    def rules(self, values):
        rules = enum.Element.rules
        self.content[self.element][rules].append(values)

    def update(self):
        writeJSON(self.content, config.FilePath.outinline)       