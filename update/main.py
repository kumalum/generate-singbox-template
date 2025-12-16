import requests
import copy
import shutil
from pathlib import Path
from config import *
import update

log = update.Log()
r_file = update.File.Read
w_file = update.File.write
process_script = update.process_script


class Downloads:

    def __init__(self):
        self.headers = Requests.headers
        self.downlaod_dir = Project.source
        self.downlaod_list = Requests.url.__dict__.items()

    def download(self):

        def __group(file_parent:Path, url:str):
            filename = url.split('/')[-1]
            file = file_parent.joinpath(filename)
            response = requests.get(url, headers=self.headers, stream=True)
            try:
                with open(file, 'wb') as code: 
                    code.write(response.content)

                log.info(f"{file.name} 保存至 {file}")
            except Exception as e: 
                log.warn(f"文件 {file.name} 保存失败. {e}")

        def __cycle_url_list(file:Path, url_list:list):
            for url in url_list: __group(file, url)

        def __create(name):
            try:
                file_parent = Path(self.downlaod_dir).joinpath(name)
                log.debug("获取本地保存地址 %s"%file_parent)

                if file_parent.exists(): return file_parent

                file_parent.mkdir(parents=True, exist_ok=True)
                log.debug("地址 %s 创建成功"%file_parent)
            except PermissionError as e:
                log.error("权限不足，无法创建文件夹 %s"%name)
            
            return file_parent

        for group_name, url_lsit in self.downlaod_list:
            if "site_" not in group_name: continue
            if not url_lsit: continue

            log.debug(f"获取组名称 {group_name} 和 下载列表 {url_lsit}")
            file_parent = __create(group_name)
            __cycle_url_list(file_parent, url_lsit)

class ToJosn:

    def __init__(self):
        source = Project.source
        self.source_group_dir = [f for f in Path(source).iterdir() if f.is_dir()]

    def srs(self):
        srs_list = [f for d in self.source_group_dir for f in d.glob("*.srs") if f.is_file()]
        for file in srs_list:
            log.debug("获取文件路径 %s"%file)
            file = str(file)
            output = file.replace(".srs", ".json")
            if Path(output).exists():
                log.debug(f"已存在，无需再次转换 {output}")
                continue
            sing_box = Program.sing_box
            cmd = [sing_box, "rule-set", "decompile", file, "-o", output]
            result = process_script(cmd)
            if result:
                log.info(f"转换文件至{output}")
            else:
                log.error(f"文件 {file} 转换失败")

class MergeJsonConfig:

    def __init__(self):
        self.source_dir = Path(Project.source)
        self.group = [f for f in self.source_dir.iterdir() if f.is_dir()]

    def merge(self):

        def deduplica_marge(old_rule, new_rule):
            
            old_rules = copy.deepcopy(old_rule['rules'][0])
            new_rules = new_rule['rules'][0]
            for rules in new_rules:
                try:
                    old_rules[rules]
                    old_rules = list(set(old_rules[rules] + new_rules[rules]))

                except KeyError:
                    old_rule[rules] = new_rules[rules]

            old_rule['rules'][0] = old_rules
            return old_rule

        for dir in self.group:
            group_content = None
            jsonfile = dir.rglob("*.json")
            dst_file = self.source_dir.joinpath("%s.json"%dir)
            jsonfile_list = list(jsonfile)
            if len(jsonfile_list) == 1:
                src_file = Path(jsonfile_list[0])
                try:
                    shutil.copyfile(src_file, dst_file)
                    log.info("复制文件到 %s"%dst_file)
                except shutil.SameFileError:
                    log.error("源文件和目标文件相同 %s"%src_file)
                except FileExistsError as e:
                    log.error("文件不存在，%s"%e)
                
                continue
            
            for file in jsonfile:
                rule_set = r_file(file).json()
                if not group_content: group_content = rule_set; continue

                group_content = deduplica_marge(group_content, rule_set)

            w_file(dst_file).json(group_content)
            log.info(f"合并规则集 {dir.name} 至 {dst_file}")

class Generate:

    def __init__(self, mode='dns'):
        self.template_content = r_file(Project.template).json()
        self.configs_dir = Path(Project.configs)
        source_dir = Path(Project.source)
        self.source_set = [f for f in source_dir.iterdir() if f.is_file()]

        self.mode = mode

    def inline(self):
        
        for set_file in self.source_set:
            set_content =  r_file(set_file).json()
            tag = set_file.stem

            if self.mode == 'dns' and "gfw" in tag: continue

            if self.mode == 'gfw' and 'gfw' not in tag: continue

            new_set = {
                "type": "inline",
                "tag": tag.replace("_", "-"),
                "rules": set_content['rules'] 
            }

            self.template_content['route']['rule_set'].append(new_set)

    def dns(self):

        def dns_diver():
            cn_tag = []; not_cn_tag = []; ad_tag = []
            for set_file in self.source_set:
                log.debug("获取配置文件%s"%set_file)
                tag = set_file.stem.replace("_", '-')
                log.debug("获取 rules tag 名称 %s"%tag)

                if  "-cn" in tag:
                    cn_tag.append(tag)
                elif "-ad" in tag:
                    ad_tag.append(tag)
                else:
                    if "gfw" in tag: continue
                    not_cn_tag.append(tag)


            log.debug("获取国内规则集 %s"%cn_tag)
            log.debug("获取国外规则集 %s"%not_cn_tag)
            log.debug("获取广告规则集 %s"%ad_tag)
            # 创建 route.rules 规则
            route = self.template_content['route']['rules']
            route_not_cn = {
                "rule_set": not_cn_tag,
                "action": "route",
                "outbound": "select"
            }
            route.append(route_not_cn)

            route_cn = {
                "domain_suffix": [
                    "1210923.xyz",
                    "kumanine.dpdns.org"
                    ],
                "rule_set": cn_tag,
                "action": "route",
                "outbound": "out_direct"
            }
            route.append(route_cn)

            route_ad = {
                "rule_set": ad_tag,
                "action": "reject"
            }
            route.append(route_ad)

            self.template_content['route']['rules'] = route
            log.info("完成 route.rules 规则集设置")
            # 设置 dns.rules 规则
            dns_rules = self.template_content['dns']['rules']

            dns_rules_not_cn = {
                "rule_set": not_cn_tag,
                "action": "route",
                "server": "dns_dot_Google"
            }
            dns_rules.append(dns_rules_not_cn)

            dns_rules_cn = {
                "rule_set": cn_tag,
                "action": "route",
                "server": "dns_dot_Ali"
            }
            dns_rules.append(dns_rules_cn)

            dns_rules_ad = {
                "rule_set": ad_tag,
                "action": "route",
                "server": "dns_block"
            }
            dns_rules.append(dns_rules_ad)
            log.info("完成 dns.rules 规则集设置")

        if self.mode == "dns":
            dns_diver()

    def platform(self):

        def android():
            self.template_content['route']['override_android_vpn'] = True
            out_path = self.configs_dir.joinpath("android_config_dns.json")
            w_file(out_path).json(self.template_content)

        def windows():
            self.template_content['route']['override_android_vpn'] = False
            out_path = self.configs_dir.joinpath("windows_config_dns.json")
            w_file(out_path).json(self.template_content)

        android()
        windows()
        
# class SingBoxConfig:

#     def __init__(self):
#         self.data = None
#         self.src = None
#         self.path = None
        
#     def run(self, cmd:list):

#         print(cmd)
#         try:
#             result = subprocess.run(cmd, capture_output=True, text=True,
#                 encoding='utf-8',errors='ignore')
            
#             if result.returncode == 0:
#                 print(f"命令执行成功 {result.stdout}")
#             else: raise Exception(result.stderr)
#             return True
#         except Exception as e:
#             print(f"命令执行失败，检查输入{e}")
#             return False    

#     def delete(self, path):

#         file = Path(path)
#         if file.exists():
#             try: file.unlink(); print(f"{path}文件已删除")
#             except PermissionError:
#                 print(f"{path}文件删失败，权限不足"); return False
#         else:
#             print(f"{path}文件不存在，请检查路径")
            
#             return True

#     def config_convert_and_delete(self):

#         # 写入文件
#         write_config(self.path, self.src)
#         # 将源文件转换为 binary
#         self.run(["./sing-box.exe", 'rule-set', 'compile', self.path])
#         # 删除文件
#         # self.delete(self.path)

#     def downlaod(self, url, index=0, type="text"):

#         res = requests.get(url, headers=HEARDE)

#         if res.status_code != 200:
#             index += 1
#             if index <= 3:
#                 print(f"文件下载失败，第{index}次尝试")
#                 self.downlaod(url, index=index)
#             else:
#                 raise Exception("网络错误，检查网址是否正确")
        
#         if type == "text":
#             self.data = res.text
#         elif type == 'json':
#             self.data = res.json()
#         else:
#             pass
        
#     def cn_ip_cidr(self):
#         if self.debug and self.debug != self.cn_ip_cidr.__name__: return
#         config_path = 'geoip@cn.json'

#         src = copy.deepcopy(CONFIG.IPCIDR)

#         # 下载元数据并转换为 ip_cidr
#         try: self.downlaod(url=CONFIG.CNIPURL)
#         except Exception: return
        
#         try: ip_cidr = self.data.split("\n")[:-1]
#         except Exception as e:
#             print(f"元数据格式不正确，请检查数据格式{self.data}\n{e}")
#             return
#         src["rules"][0]["ip_cidr"] = ip_cidr

#         # 写入数据
#         write_config(config_path, src)
#         # 将源文件转换为 binary
#         flag = self.run(["./sing-box.exe", 'rule-set', 'compile', "./geoip@cn.json"])

#         # 删除源文件
#         if flag: self.delete(config_path)

#     def microsoft(self):
#         url = "https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7"
#         self.path = "microsoft-sharepoint@global.json"

#         # 获取原始数据 self.data
#         self.downlaod(url=url, type='json')
#         domain_src = []; domain_suffix = []; domain = []; ips = []
#         # 格式化数据 转换为 {"ip_cidr":[], "domain":[], "domain_suffix":[]}
#         for data in self.data:
#             if data['serviceArea'] == 'SharePoint':
#                 try: domain_src += data['urls']
#                 except: pass
                
#                 try: ips += data['ips']
#                 except: pass

#         for df in domain_src:
#             if "*" in df:
#                 domain_suffix.append(df[2:])
#             else:
#                 domain.append(df)

#         self.src = copy.deepcopy(CONFIG.IPCIDR)
#         self.src["rules"][0]["ip_cidr"] = ips
#         self.src["rules"][0]["domain"] = domain
#         self.src["rules"][0]["domain_suffix"] = domain_suffix

#         print(json.dumps(self.src, indent=4, ensure_ascii=False))
#         self.config_convert_and_delete()

#     def loyalsoldier_clash_rules(self):

#         def get_domain_or_cidr(now_data):
#             import re

#             pattern = r"'([^']+)'" 
#             result = re.findall(pattern, now_data)
#             # 如果需要过滤掉空字符串
#             now_data = [s for s in result if s]
#             return now_data


#         path = "C:/Users/blsm/github/clash-rules"
#         file = [Path(f).resolve() for f in Path(path).iterdir() if f.is_file() and f.suffix == ".txt"]

#         for p in file:

#             self.path = str(p).replace(".txt", ".json")
#             self.src = copy.deepcopy(CONFIG.RULES)
#             now_data = read_txt(p)
#             now_data = get_domain_or_cidr(now_data)
            
#             if "cidr" in p.name:
#                 self.src["rules"][0] = { 'ip_cidr': now_data}
                
#             else:
#                 rule = {}
#                 for self.data in now_data:
#                     if "+." in self.data:
#                         # print(1)
#                         try: rule['domain_suffix']
#                         except KeyError: rule['domain_suffix'] = []
#                         rule['domain_suffix'].append(self.data.replace("+.", ""))
#                     else:
#                         try: rule['domain']
#                         except KeyError: rule['domain'] = []
#                         rule['domain'].append(self.data)
                    
#                     self.src["rules"][0] = rule
#                     # print(self.src)

                    
            
#             self.config_convert_and_delete()


                
            
        

            



    # def github(self):
    #     if self.debug and self.debug != self.github.__name__: return
    #     # 下载原始数据
    #     src = requests.get(url=self.github_hosts_url, headers=HEARDE).text
    #     # 格式化数据， {domain: ip}
    #     src_hosts = src.split("\n")[4:-7]
    #     hosts = {}
    #     for host in src_hosts:
    #         host_split = host.split(" "); hosts[host_split[-1]] = str(host_split[0])

    #     # 将 hosts 写入到 dns.servers
    #     self.get_index(self.data['dns']['servers'], 'tag', 'hosts_github')
    #     self.data['dns']['servers'][self.index]['predefined'] = hosts
        
    #     # # 将 domain 写入到 route.rule_set
    #     self.get_index(self.data['route']['rule_set'], 'tag', 'geosite-github')
    #     self.__route_inline_rules('domain', list(hosts.keys()))
    
    # def __call__(self):
    #     # self.cn_ip_cidr()
    #     # self.microsoft()
    #     self.loyalsoldier_clash_rules()
    #     # self.github()