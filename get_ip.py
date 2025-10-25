import requests
import re
import configparser
import os
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def get_config_from_env():
    """从环境变量获取敏感配置"""
    env_config = {}
    
    # Cloudflare 敏感信息配置
    cf_sensitive_mapping = {
        'CLOUDFLARE_API_TOKEN': 'api_token',
        'CLOUDFLARE_ZONE_ID': 'zone_id', 
        'CLOUDFLARE_DOMAIN': 'domain'
    }
    
    cf_config = {}
    for env_var, config_key in cf_sensitive_mapping.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            cf_config[config_key] = value
            print(f"从环境变量获取 {config_key}")
    
    # 如果设置了任意 Cloudflare 敏感环境变量，则启用 Cloudflare
    if any(key in os.environ for key in cf_sensitive_mapping.keys()):
        cf_config['enable'] = True
    else:
        cf_config['enable'] = False
    
    return {'cloudflare': cf_config}

def merge_configs(file_config, env_config):
    """合并文件配置和环境变量配置（环境变量优先级更高）"""
    merged_config = configparser.ConfigParser()
    
    # 复制文件配置
    for section in file_config.sections():
        if section not in merged_config:
            merged_config.add_section(section)
        for key, value in file_config.items(section):
            merged_config.set(section, key, value)
    
    # 用环境变量配置覆盖敏感信息
    for section, settings in env_config.items():
        if section not in merged_config:
            merged_config.add_section(section)
        for key, value in settings.items():
            if isinstance(value, bool):
                merged_config.set(section, key, str(value).lower())
            else:
                merged_config.set(section, key, str(value))
    
    return merged_config

def main():
    # 创建输出目录
    output_dir = create_output_directory()
    
    # 读取配置文件
    file_config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        print("未找到 config.ini 文件")
        print("请创建 config.ini 文件并配置链接")
        return
    
    # 修复编码问题
    try:
        with open('config.ini', 'r', encoding='utf-8') as f:
            file_config.read_file(f)
    except UnicodeDecodeError:
        try:
            with open('config.ini', 'r', encoding='gbk') as f:
                file_config.read_file(f)
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return
    
    # 从环境变量获取敏感配置
    env_config = get_config_from_env()
    
    # 合并配置
    config = merge_configs(file_config, env_config)
    
    # 获取User-Agent设置
    user_agent = None
    if config.has_section('settings') and 'user_agent' in config['settings']:
        user_agent = config['settings']['user_agent']
        print(f"使用 User-Agent: {user_agent}")
    
    # 获取线路类型配置
    include_lines = None
    if config.has_section('settings') and 'include_lines' in config['settings']:
        line_config = config['settings']['include_lines']
        include_lines = parse_line_config(line_config)
        if include_lines:
            print(f"提取线路: {', '.join(include_lines)}")
        else:
            print("未配置有效线路类型，将提取所有线路")
    else:
        print("未配置线路类型，将提取所有线路")
    
    # 获取Cloudflare配置
    cf_config = {}
    if config.has_section('cloudflare'):
        cf_config = {
            'enable': config.getboolean('cloudflare', 'enable', fallback=False),
            'api_token': config.get('cloudflare', 'api_token', fallback=''),
            'zone_id': config.get('cloudflare', 'zone_id', fallback=''),
            'domain': config.get('cloudflare', 'domain', fallback=''),
            'record_name': config.get('cloudflare', 'record_name', fallback='cf'),
            'record_type': config.get('cloudflare', 'record_type', fallback='A'),
            'ttl': config.getint('cloudflare', 'ttl', fallback=1),
            'proxied': config.getboolean('cloudflare', 'proxied', fallback=False),
            'max_records_per_line': config.getint('cloudflare', 'max_records_per_line', fallback=5)
        }
        
        # 检查敏感信息是否完整
        if cf_config['enable']:
            missing_fields = []
            if not cf_config['api_token']:
                missing_fields.append('api_token')
            if not cf_config['zone_id']:
                missing_fields.append('zone_id')
            if not cf_config['domain']:
                missing_fields.append('domain')
            
            if missing_fields:
                print(f"警告: Cloudflare 配置不完整，缺少: {', '.join(missing_fields)}")
                print("Cloudflare DNS 更新功能将被禁用")
                cf_config['enable'] = False
    
    # 获取链接列表
    if not config.has_section('links'):
        print("配置文件中缺少 [links] 部分")
        return
    
    all_ip_lists = []
    
    # 处理每个链接
    for key in config['links']:
        url = config['links'][key]
        if url and url.strip():  # 只处理非空URL
            ip_list = process_link(url, output_dir, key, user_agent, include_lines)
            
            if ip_list:
                all_ip_lists.append(ip_list)
        else:
            print(f"跳过空链接: {key}")
    
    # 合并并去重所有IP地址
    if all_ip_lists:
        merged_ips = merge_and_deduplicate_files(all_ip_lists, output_dir)
        print(f"\n合并后共 {len(merged_ips)} 个唯一IP地址")
        
        # 更新Cloudflare DNS记录
        update_cloudflare_dns(merged_ips, cf_config)
    else:
        print("\n未找到任何IP地址")

if __name__ == "__main__":
    main()