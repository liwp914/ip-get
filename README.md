# **Cloudflare DNS IP 更新工具**

这是一个自动化的 Cloudflare IP 地址获取和 DNS 更新工具，能够定期从多个源获取最新的 Cloudflare IP 地址，并自动更新到 Cloudflare DNS 记录中。

## **功能特性**

- 🔄 **自动获取 IP**：从多个公开源获取最新的 Cloudflare IP 地址
- 📊 **线路分类**：支持电信、联通、移动、多线、IPv6 等线路类型
- 🌐 **DNS 自动更新**：自动更新 Cloudflare DNS 记录
- ☁️ **多平台同步**：支持 WebDAV 和 Cloudflare KV 存储同步
- ⏰ **定时任务**：每6小时自动运行一次
- 🔒 **安全配置**：通过环境变量保护敏感信息

## **快速开始**

### **1. 克隆项目**

```
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### **2. 安装依赖**

```
pip install -r requirements.txt
```

### **3. 配置环境变量**

创建 `.env`文件并配置必要的参数：

```
# Cloudflare IP 源链接（必填）CF1=https://api.urlce.com/cloudflare.html
CF2=https://stock.hostmonit.com/CloudFlareYes

# 线路类型配置（可选，默认提取所有线路）INCLUDE_LINES=电信,联通,移动,多线,IPV6

# Cloudflare DNS 更新配置（可选）CLOUDFLARE_ENABLE=false
CLOUDFLARE_RECORD_NAME=cf
CLOUDFLARE_TTL=1
CLOUDFLARE_PROXIED=false
CLOUDFLARE_MAX_RECORDS_PER_LINE=5

# 其他配置（可选）USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36TIMEOUT=30
```

### **4. 设置 GitHub Secrets**

在 GitHub 仓库的 **Settings > Secrets and variables > Actions** 中添加以下 Secrets：

| **Secret 名称** | **描述** | **是否必填** |
| --- | --- | --- |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token | 是 |
| `CLOUDFLARE_ZONE_ID` | Cloudflare Zone ID | 是 |
| `CLOUDFLARE_DOMAIN` | 您的域名 | 是 |
| `CF1` | 第一个 Cloudflare IP 源链接 | 是 |
| `CF2` | 第二个 Cloudflare IP 源链接 | 是 |
| `INCLUDE_LINES` | 线路类型配置 | 否 |
| `WEBDAV_URL` | WebDAV 服务器地址 | 否 |
| `WEBDAV_USERNAME` | WebDAV 用户名 | 否 |
| `WEBDAV_PASSWORD` | WebDAV 密码 | 否 |
| `CFKV_DOMAIN` | Cloudflare KV 域名 | 否 |
| `CFKV_TOKEN` | Cloudflare KV Token | 否 |

### **5. 手动运行**

```
python cfdns_ip.py
```

## **输出文件**

工具运行后会在 `output/`目录生成以下文件：

- `cf1.txt`从第一个源获取的 IP 列表
- `cf2.txt`从第二个源获取的 IP 列表
- `all_cf_ip.txt`合并去重后的所有 IP 列表

文件格式示例：

```
1.1.1.1#电信
1.0.0.1#联通
2606:4700:4700::1111#IPV6
```

## **DNS 记录生成规则**

工具会根据线路类型自动创建对应的 DNS 记录：

| **线路类型** | **子域名示例** | **说明** |
| --- | --- | --- |
| 电信 | `cf-CT.yourdomain.com` | China Telecom |
| 联通 | `cf-CU.yourdomain.com` | China Unicom |
| 移动 | `cf-CM.yourdomain.com` | China Mobile |
| 多线 | `cf-multi.yourdomain.com` | 多线接入 |
| IPV6 | `cf-ipv6.yourdomain.com` | IPv6 地址 |

## **自定义配置**

### **修改运行频率**

编辑 `.github/workflows/update-dns.yml`文件中的 cron 表达式：

```
schedule:
  - cron: '0 */6 * * *'# 每6小时运行一次
```

常用时间表达式：

- `0 */6 * * *`每6小时
- `0 */12 * * *`每12小时
- `0 0 * * *`每天午夜
- `0 0 * * 0`每周日午夜

### **添加更多 IP 源**

在 `.env`文件中添加更多源：

```
CF3=https://third-source.com/cloudflare-ips
```

### **自定义线路类型**

修改 `INCLUDE_LINES`配置来选择需要的线路：

```
INCLUDE_LINES=电信,联通# 只提取电信和联通线路
```

## **故障排除**

### **常见问题**

1. **"未配置任何链接"错误**
    - 检查 `CF1`和 `CF2`是否在 `.env`文件或 GitHub Secrets 中正确配置
2. **Cloudflare API 错误**
    - 验证 API Token 是否有足够的 DNS 编辑权限
    - 检查 Zone ID 和域名是否正确
3. **IP 获取失败**
    - 检查源链接是否可访问
    - 查看网络连接是否正常

### **查看日志**

GitHub Actions 运行日志可在仓库的 **Actions** 标签页查看。

### **手动测试**

```
# 测试环境变量加载
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('CF1:', os.getenv('CF1'))"

# 测试单个功能
python -c "import cfdns_ip; print('模块导入成功')"
```

## **许可证**

本项目采用 MIT 许可证。详见 LICENSE文件。

## **贡献**

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## **免责声明**

本项目仅供学习和研究使用，请遵守相关服务条款：

- Cloudflare API 使用请遵守 Cloudflare 服务条款
- 请合理使用公共 IP 资源，避免对源站造成过大压力

## **更新日志**

### **v1.0.0**

- 初始版本发布
- 支持多源 IP 获取
- 自动 DNS 记录更新
- WebDAV 和 Cloudflare KV 同步功能

---

如有问题，请查看 GitHub Issues或提交新的 Issue。
