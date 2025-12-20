from pathlib import Path

class FilePath:
    __env = Path.cwd()
    if __env.parent == "singbox":
        root = __env.parent.parent.joinpath('rule-set')
        config_dir = __env
    else:
        root = __env.joinpath('rule-set')
        config_dir = __env.joinpath("singbox")

    __base = config_dir.joinpath('base')
    pref_example = __base.joinpath('pref.example.toml')
    template = __base.joinpath('template.json')

    output = config_dir.joinpath("output")
    outremote = output.joinpath('remote_rule_set.json')
    outinline = output.joinpath('inline_rule_set.json')
    
class Github:
    api = "https://api.github.com/repos/9lit/config-singbox/contents?ref=rule-set"
    adguard = "https://raw.githubusercontent.com/9lit/config-singbox/rule-set/adguard.srs"