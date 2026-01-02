import requests
import argparse
import os
import shutil
from update import logging
from update import config, enum
from update import process_script as script, readJSON

def download_rule_set(urls):

    # 获取下载地址， 并创建文件夹
    download_dir = config.FilePath.downloads.joinpath(urls)
    try:
        if not download_dir.exists(): 
            download_dir.mkdir(parents=True, exist_ok=True)
            logging.debug("创建成功")
    except PermissionError as e:
        logging.error("权限不足，无法创建文件夹，跳过本次下载")


    # 下载文件
    for url in download_urls[urls]:
        filename = url.split("/")[-1]
        if len(filename.split(".")) == 1:
            filename = filename + ".txt"
        path = download_dir.joinpath(filename)
        response = requests.get(url, stream=True)
        
        with open(path, 'wb') as b: b.write(response.content)
        logging.info("成功下载文件：%s"%filename)

def merge_json():
    """ 合并同类型的规则文件，即配置文件 pref.example.toml 中 downloads 同列表的规则 """
    json_list = [f for f in file_path.downloads.rglob("*") if f.is_file and f.suffix == enum.Suffix.json]

    for fjson in json_list:
        rule_set_file_name = fjson.parent.with_suffix(enum.Suffix.json).name
        rule_set_file = file_path.output.joinpath(rule_set_file_name)

        old_rules_content = readJSON(rule_set_file)
        new_rules_content = readJSON(fjson)

        new_rules = new_rules_content[enum.RuleSet.rules][0]
        old_rules = old_rules_content[enum.RuleSet.rules][0]
        
        for rule in new_rules:
            if rule in old_rules_content:
                old_rules[rule] = list(set(new_rules[rule] + old_rules[rule]))
            else:
                old_rules[rule] = new_rules[rule]

def to_json():
    srs_list = [f for f in config.FilePath.downloads.rglob("*") if f.is_file and f.suffix == enum.Suffix.srs]
    for fsrs in srs_list:

        fjson = fsrs.with_suffix(enum.Suffix.json)
        cmd = [program, "rule-set", "decompile", fsrs, "-o", fjson]
        script(cmd)

def to_binary():
    json_list = [f for f in config.FilePath.output.iterdir() if f.is_file and f.suffix == enum.Suffix.json]
    for fjson in json_list:

        fsrs = fjson.with_name(f'site-{fjson.name.replace("_","-")}').with_suffix(enum.Suffix.srs)
        cmd = [program, "rule-set", "compile", fjson, "-o", fsrs]
        script(cmd)

def binary_adguard():
    adguard = file_path.adguard_file
    if not adguard.exists():
        logging.info("adguard 的默认位置不存在，开始搜索文件")
        all_file = config.FilePath.output.rglob("*")

        for f in all_file:
            if f.is_file and f.parent.name == enum.groups.adguard: adguard = f

    srs_adguard = file_path.output.joinpath(enum.groups.adguard).with_suffix(enum.Suffix.srs)

    cmd = [program, "rule-set", "convert", "--type", "adguard", "--output", srs_adguard, adguard]
    script(cmd)
    logging.info("adguard 文件转换成功")

def clear_cache():

    if not file_path.output.exists(): return
    shutil.rmtree(file_path.output)

def write(name, link):
    """将 rule-set 连接写入缓存文件"""
    with open(file_path.rule_set_remote_url_set, 'a+') as f: 
        f.writelines(f"site-{name}={link}\n")

def run(clear_file:str):

    if clear_file.upper() == "Y" : clear_cache()

    for urls in download_urls:

        link = download_urls[urls]
        repo_rule_set_name = urls.replace("_", "-")

        if urls == enum.groups.adguard or len(link) != 1: 
            download_rule_set(urls)
            repo_rule_set = repo + "/" + repo_rule_set_name + enum.Suffix.srs
            write(repo_rule_set_name, repo_rule_set)
            continue
        
        write(repo_rule_set_name, link[0])

    len_downloads = len(list(file_path.downloads.iterdir()))

    if len_downloads > 2: 
        to_json(); merge_json(); to_binary()
    else:
        logging.info("没有可合并的文件")

    binary_adguard()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("clear_file", default="Y", help="Y/n，清除缓存文件，默认为 Y。")
    options = parser.parse_args()

    file_path = config.FilePath
    repo = config.pref_update[enum.Pref.repo]
    download_urls = config.pref_update[enum.Pref.downloads]
    program = config.pref_update[enum.Pref.program][enum.Pref.singbox]

    run(options.clear_file)