from pathlib import Path
import tomllib

class FilePath:
    __work = Path().cwd()
    __root = __work.joinpath('update')
    __base = __root.joinpath("base")

    pref_file = __base.joinpath("pref.update.toml")
    output = __work.joinpath("rule-set")
    downloads = output.joinpath("downloads")
    rule_set_remote_url_set = __work.joinpath("singbox", "base", "url_set.txt")
    adguard_file = downloads.joinpath('adguard', "blocklist.txt")


# 读取文件配置
with open(FilePath.pref_file, 'rb') as f: 
    pref_update = tomllib.load(f)


