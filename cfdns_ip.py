import requests
import re
import os
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

def create_output_directory():
    """创建输出目录"""
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def get_webpage_content(url, user_agent=None):
    """获取网页内容"""
    try:
        headers = {
            'User-Agent': user_agent if user_agent else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=int(os.getenv('TIMEOUT', 30)))
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"获取网页内容失败: {e}")
        return None

def extract_ips_from_content(content, include_lines=None):
    """从网页内容中提取IP地址和线路信息"""
    results = []
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # 查找包含IP地址的文本
    text_content = soup.get_text()
    
    # 使用正则表达式匹配IP地址和线路
    # 格式: 序号 线路 IP地址 丢包 延迟 速度 带宽 Colo 时间
    pattern = r'(\d+)\s+([^\s]+)\s+([\d\.:a-fA-F]+)\s+[^\s]+\s+[^\s]+\s+[^\s]+\s+[^\s]+\s+[^\s]+\s+[^\s]+'
    matches = re.finditer(pattern, text_content)
    
    for match in matches:
        line_type = match.group(2)  # 线路类型
        ip = match.group(3)         # IP地址
        
        # 根据配置决定是否提取该线路类型的IP地址
        if include_lines and line_type not in include_lines:
            continue  # 跳过不在允许列表中的线路类型
            
        results.append(f"{ip}#{line_type}")
    
    return results

def save_to_file(data, filename):
    """将数据保存到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(f"{item}\n")
    print(f"已保存 {len(data)} 个IP地址到 {filename}")

def process_link(url, output_dir, link_name, user_agent=None, include_lines=None):
    """处理单个链接"""
    print(f"\n处理链接: {url}")
    
    # 获取网页内容
    content = get_webpage_content(url, user_agent)
    if not content:
        print("无法获取网页内容，跳过")
        return []
    
    # 提取IP地址
    ip_list = extract_ips_from_content(content, include_lines)
    
    if not ip_list:
        print("未找到任何IP地址")
        return []
    
    print(f"找到 {len(ip_list)} 个IP地址")
    
    # 生成文件名（不包含日期信息）
    filename = os.path.join(output_dir, f"{link_name}.txt")
    
    # 保存到文件
    save_to_file(ip_list, filename)
    
    return ip_list

def sort_ip_list(ip_list):
    """对IP地址列表进行排序"""
    # 首先按线路类型排序
    line_order = {
        '电信': 1,
        '联通': 2,
        '移动': 3,
        '多线': 4,
        'IPV6': 5
    }
    
    def sort_key(item):
        # 分离IP和线路
        parts = item.split('#')
        ip = parts[0]
        line = parts[1] if len(parts) > 1 else ''
        
        # 获取线路排序值
        line_value = line_order.get(line, 99)
        
        # 对于IPv4地址，转换为数字进行排序
        if '.' in ip:
            ip_parts = ip.split('.')
            ip_numeric = tuple(int(part) for part in ip_parts)
            return (line_value, ip_numeric)
        else:
            # 对于IPv6地址，按字符串排序
            return (line_value, ip)
    
    return sorted(ip_list, key=sort_key)

def merge_and_deduplicate_files(file_lists, output_dir):
    """合并并去重所有IP地址"""
    all_ips = set()
    
    for ip_list in file_lists:
        all_ips.update(ip_list)
    
    # 对IP地址进行排序
    sorted_ips = sort_ip_list(list(all_ips))
    
    # 生成合并后的文件名
    filename = os.path.join(output_dir, "all_cf_ip.txt")
    
    # 保存到文件
    save_to_file(sorted_ips, filename)
    
    return sorted_ips

def parse_line_config(config_str):
    """解析线路配置字符串"""
    if not config_str:
        return None
    
    # 支持逗号、空格、分号分隔
    lines = re.split(r'[,;\s]+', config_str)
    # 去除空字符串
    lines = [line.strip() for line in lines if line.strip()]
    
    # 映射可能的别名
    line_mapping = {
        '电信': '电信',
        '联通': '联通',
        '移动': '移动',
        '多线': '多线',
        'ipv6': 'IPV6',
        'IPv6': 'IPV6',
        'IPV6': 'IPV6'
    }
    
    # 转换为标准名称
    standardized_lines = []
    for line in lines:
        if line in line_mapping:
            standardized_lines.append(line_mapping[line])
        else:
            print(f"警告: 未知的线路类型 '{line}'，已忽略")
    
    return standardized_lines if standardized_lines else None

def get_line_type_mapping():
    """获取线路类型到子域名的映射"""
    return {
        '电信': 'CT',
        '联通': 'CU',
        '移动': 'CM',
        '多线': 'multi',
        'IPV6': 'ipv6'
    }

def check_token_permissions(headers):
    """检查API令牌的权限"""
    print("检查API令牌权限...")
    
    # 获取令牌详细信息
    verify_url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
    try:
        response = requests.get(verify_url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                token_info = result['result']
                print(f"令牌状态: {token_info.get('status', '未知')}")
                
                # 检查权限
                policies = token_info.get('policies', [])
                for policy in policies:
                    resources = policy.get('resources', {})
                    for resource_id, permission in resources.items():
                        if 'dns' in resource_id.lower() or 'zone' in resource_id.lower():
                            print(f"资源: {resource_id}, 权限: {permission}")
                
                return True
            else:
                print(f"令牌验证失败: {result.get('errors', [{}])[0].get('message', '未知错误')}")
                return False
        else:
            print(f"令牌验证失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"检查令牌权限时出错: {e}")
        return False

def update_cloudflare_dns(ips, cf_config):
    """更新Cloudflare DNS记录，按线路类型创建子域名"""
    if not cf_config.get('enable', False):
        print("Cloudflare DNS更新未启用")
        return
    
    print("\n开始更新Cloudflare DNS记录...")
    
    # 提取API配置
    api_token = cf_config.get('api_token')
    zone_id = cf_config.get('zone_id')
    domain = cf_config.get('domain')
    base_record_name = cf_config.get('record_name', 'cf')
    record_type = cf_config.get('record_type', 'A')
    ttl = cf_config.get('ttl', 1)  # 1 = auto, 60-86400 for manual TTL
    max_records_per_line = cf_config.get('max_records_per_line', 5)
    proxied = cf_config.get('proxied', False)
    
    if not all([api_token, zone_id, domain]):
        print("Cloudflare配置不完整，跳过DNS更新")
        return
    
    # 验证API令牌格式
    if len(api_token) != 40:
        print(f"API令牌长度异常 ({len(api_token)}字符)，应为40字符")
        return
    
    # 验证区域ID格式
    if len(zone_id) != 32:
        print(f"区域ID长度异常 ({len(zone_id)}字符)，应为32字符")
        return
    
    # 准备API请求头
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # 验证API令牌有效性
    verify_url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
    try:
        response = requests.get(verify_url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                print("Cloudflare API令牌验证成功")
                # 检查令牌权限
                check_token_permissions(headers)
            else:
                print(f"API令牌验证失败: {result.get('errors', [{}])[0].get('message', '未知错误')}")
                return
        else:
            print(f"API令牌验证失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
    except Exception as e:
        print(f"验证API令牌时出错: {e}")
        return
    
    # 验证区域ID有效性
    zone_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
    try:
        response = requests.get(zone_url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                print(f"区域ID验证成功，域名: {result['result']['name']}")
            else:
                print(f"区域ID验证失败: {result.get('errors', [{}])[0].get('message', '未知错误')}")
                return
        else:
            print(f"区域ID验证失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
    except Exception as e:
        print(f"验证区域ID时出错: {e}")
        return
    
    # 获取线路类型到子域名的映射
    line_mapping = get_line_type_mapping()
    
    # 按线路类型分组IP
    ips_by_line = {}
    for ip_info in ips:
        parts = ip_info.split('#')
        if len(parts) < 2:
            continue
            
        ip = parts[0]
        line_type = parts[1]
        
        if line_type not in ips_by_line:
            ips_by_line[line_type] = []
        
        ips_by_line[line_type].append(ip)
    
    # 为每个线路类型创建DNS记录
    for line_type, ip_list in ips_by_line.items():
        # 获取子域名
        subdomain = line_mapping.get(line_type, line_type.lower())
        record_name = f"{base_record_name}-{subdomain}"
        
        print(f"\n处理线路类型: {line_type} -> {record_name}.{domain}")
        
        # 限制每个线路类型的记录数量
        ip_list = ip_list[:max_records_per_line]
        
        # 获取当前DNS记录
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
        params = {'name': f'{record_name}.{domain}', 'type': record_type}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    records = result.get('result', [])
                    
                    # 删除现有记录
                    for record in records:
                        record_id = record['id']
                        delete_url = f'{url}/{record_id}'
                        delete_response = requests.delete(delete_url, headers=headers)
                        if delete_response.status_code == 200:
                            print(f"已删除记录: {record['name']} -> {record['content']}")
                        else:
                            delete_result = delete_response.json()
                            print(f"删除记录失败: {delete_result.get('errors', [{}])[0].get('message', '未知错误')}")
                    
                    # 添加新记录
                    for ip in ip_list:
                        # 根据IP地址确定记录类型
                        record_type_for_ip = 'AAAA' if ':' in ip else 'A'
                        
                        # 创建记录数据
                        data = {
                            'type': record_type_for_ip,
                            'name': record_name,
                            'content': ip,
                            'ttl': ttl,
                            'proxied': proxied
                        }
                        
                        # 发送创建请求
                        create_response = requests.post(url, headers=headers, json=data)
                        if create_response.status_code == 200:
                            print(f"已添加记录: {record_name}.{domain} -> {ip} ({record_type_for_ip})")
                        else:
                            create_result = create_response.json()
                            print(f"添加记录失败: {create_result.get('errors', [{}])[0].get('message', '未知错误')}")
                else:
                    print(f"获取DNS记录失败: {result.get('errors', [{}])[0].get('message', '未知错误')}")
            else:
                print(f"获取DNS记录失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"更新{line_type}线路DNS记录时出错: {e}")

def main():
    # 创建输出目录
    output_dir = create_output_directory()
    
    # 从环境变量获取配置
    user_agent = os.getenv('USER_AGENT')
    if user_agent:
        print(f"使用 User-Agent: {user_agent}")
    
    # 获取线路类型配置
    include_lines = None
    line_config = os.getenv('INCLUDE_LINES')
    if line_config:
        include_lines = parse_line_config(line_config)
        if include_lines:
            print(f"提取线路: {', '.join(include_lines)}")
        else:
            print("未配置有效线路类型，将提取所有线路")
    else:
        print("未配置线路类型，将提取所有线路")
    
    # 获取Cloudflare配置
    cf_config = {
        'enable': os.getenv('CLOUDFLARE_ENABLE', 'false').lower() == 'true',
        'api_token': os.getenv('CLOUDFLARE_API_TOKEN', ''),
        'zone_id': os.getenv('CLOUDFLARE_ZONE_ID', ''),
        'domain': os.getenv('CLOUDFLARE_DOMAIN', ''),
        'record_name': os.getenv('CLOUDFLARE_RECORD_NAME', 'cf'),
        'record_type': os.getenv('CLOUDFLARE_RECORD_TYPE', 'A'),
        'ttl': int(os.getenv('CLOUDFLARE_TTL', 1)),
        'proxied': os.getenv('CLOUDFLARE_PROXIED', 'false').lower() == 'true',
        'max_records_per_line': int(os.getenv('CLOUDFLARE_MAX_RECORDS_PER_LINE', 5))
    }
    
    # 获取链接列表
    links = {}
    if os.getenv('CF1'):
        links['cf1'] = os.getenv('CF1')
    if os.getenv('CF2'):
        links['cf2'] = os.getenv('CF2')
    if os.getenv('CF3'):
        links['cf3'] = os.getenv('CF3')
    
    if not links:
        print("未配置任何链接")
        return
    
    all_ip_lists = []
    
    # 处理每个链接
    for key, url in links.items():
        if url:  # 确保URL不为空
            ip_list = process_link(url, output_dir, key, user_agent, include_lines)
            
            if ip_list:
                all_ip_lists.append(ip_list)
    
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