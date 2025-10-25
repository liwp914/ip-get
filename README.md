# Cloudflare IP 自动更新项目

## 安全设置说明

为了保护敏感信息，本项目使用环境变量来管理敏感配置，非敏感配置保留在 config.ini 中：

### 1. 配置结构

**通过环境变量设置的敏感信息：**
- `CLOUDFLARE_API_TOKEN` - Cloudflare API 令牌
- `CLOUDFLARE_ZONE_ID` - Cloudflare 区域 ID  
- `CLOUDFLARE_DOMAIN` - 域名
- `WEBDAV_URL` - WebDAV 服务器 URL
- `WEBDAV_USERNAME` - WebDAV 用户名
- `WEBDAV_PASSWORD` - WebDAV 密码

**在 config.ini 中设置的非敏感配置：**
- `record_name` - DNS 记录名称（默认：cf）
- `record_type` - 记录类型（默认：A）
- `ttl` - TTL 值（默认：1）
- `proxied` - 是否启用代理（默认：false）
- `max_records_per_line` - 每线路最大记录数（默认：5）

### 2. 设置步骤

**本地开发：**
1. 复制 `config.ini.example` 为 `config.ini`
2. 编辑 `config.ini` 设置非敏感配置
3. 设置环境变量存储敏感信息

**GitHub Actions：**
1. 在仓库的 Settings → Secrets and variables → Actions 中设置敏感信息环境变量
2. 在 `config.ini` 中设置非敏感配置
3. 工作流将自动运行

### 3. 初始化