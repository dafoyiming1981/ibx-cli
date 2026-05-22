# ibx-cli

Infoblox NIOS CLI toolset for DNS/DHCP management via WAPI.

## RHEL 8 安装手册 (venv 方式)

### 前置条件

- RHEL 8 操作系统
- 可访问 Infoblox Grid Master 的网络
- 具有 sudo 权限的用户

### 第一步: 安装 Python 3.9+

RHEL 8 默认 Python 为 3.6（已 EOL），需要从 AppStream 安装 Python 3.9：

```bash
# 检查可用的 Python 流
sudo dnf module list python39

# 安装 Python 3.9
sudo dnf module install python39 -y

# 确认版本
python3.9 --version
```

### 第二步: 上传安装包到测试环境

从构建主机将 whl 文件传输到 RHEL 8 测试主机：

```bash
# 在构建主机上执行
scp ibx-cli/dist/ibx_cli-0.1.0-py3-none-any.whl user@rhel8-test:/tmp/
```

或直接拷贝整个目录（含源码）：

```bash
tar czf ibx-cli.tar.gz ibx-cli/
scp ibx-cli.tar.gz user@rhel8-test:/tmp/
ssh user@rhel8-test "cd /tmp && tar xzf ibx-cli.tar.gz"
```

### 第三步: 创建 venv 并安装

```bash
# SSH 到 RHEL 8 测试主机
ssh user@rhel8-test

# 创建 Python 虚拟环境
python3.9 -m venv ~/ibx-env

# 激活虚拟环境
source ~/ibx-env/bin/activate

# 验证 pip 版本
pip --version

# 安装 ibx-cli
pip install /tmp/ibx_cli-0.1.0-py3-none-any.whl

# 验证安装
ibx --version
```

### 第四步: 配置 Infoblox 连接

```bash
# 生成示例配置文件
ibx config init

# 编辑配置文件
vi ~/.infoblox/config
```

编辑 `~/.infoblox/config`，填入实际的 Infoblox 地址和凭据：

```yaml
defaults:
  host: 10.x.x.x          # 替换为你的 Infoblox Grid Master IP
  username: admin          # 替换为你的用户名
  password: your_password  # 替换为你的密码
  wapi_version: "2.13"
  ssl_verify: false        # 自签名证书设为 false
  timeout: 30
  max_results: 1000
```

设置配置文件权限（保护密码）：

```bash
chmod 600 ~/.infoblox/config
```

### 第五步: 验证连接

```bash
# 测试到 Infoblox 的连接
ibx config test-connection
```

成功输出示例：

```
Connecting to 10.x.x.x...
Connected successfully!
  Grid: infoblox-grid
  WAPI version: 2.13
```

### 可选: 使用环境变量（不写配置文件）

```bash
export IBX_HOST=10.x.x.x
export IBX_USERNAME=admin
export IBX_PASSWORD=your_password

# 直接运行命令，无需配置文件
ibx dns zones
```

### 退出 venv

```bash
deactivate
```

### 下次使用时快速启动

```bash
source ~/ibx-env/bin/activate
ibx dns zones
```

---

## 通用安装（开发模式）

```bash
cd ibx-cli
pip install -e .
```

## Configuration

### Quick start

```bash
ibx config init
# Edit ~/.infoblox/config with your Infoblox credentials
```

### Config file format (~/.infoblox/config)

```yaml
defaults:
  host: infoblox.example.com
  username: admin
  wapi_version: "2.13"
  ssl_verify: false
  timeout: 30
  max_results: 1000

profiles:
  prod:
    host: infoblox-prod.example.com
  lab:
    host: infoblox-lab.example.com
    ssl_verify: false
```

### Environment variables (alternative)

```bash
export IBX_HOST=infoblox.example.com
export IBX_USERNAME=admin
export IBX_PASSWORD=your_password
```

### CLI flags (highest priority)

```bash
ibx --host 10.0.0.2 --username admin --password secret dns zones
```

## Usage

### DNS Commands

```bash
# List all A records
ibx dns a

# Filter by name (supports --regex)
ibx dns a --name "www.example.com"

# Search within a zone
ibx dns a --zone "example.com" --view "internal"

# List all records in a zone
ibx dns all-records --zone "example.com"

# List authoritative zones
ibx dns zones --view "default"

# List host records
ibx dns hosts --name "server1"

# Other record types
ibx dns cname --name "alias"
ibx dns mx --zone "example.com"
ibx dns txt --name "_dmarc"
ibx dns ptr --ipv4addr "10.0.0.1"
ibx dns aaaa --name "ipv6host"
```

### DHCP Commands

```bash
# List IPv4 networks
ibx dhcp networks

# Filter by CIDR
ibx dhcp networks --network "10.0.0.0/24"

# List fixed addresses
ibx dhcp fixed-address --mac "00:11:22:33:44:55"

# List DHCP leases
ibx dhcp leases --state active --limit 50

# List IPv4 address usage
ibx dhcp ipv4-addresses --network "10.0.0.0/24" --status used

# List IPv6 networks
ibx dhcp ipv6-networks

# List network containers
ibx dhcp containers
```

### Infrastructure Commands

```bash
# Show grid properties
ibx infra grid

# List grid members
ibx infra members

# List DNS views
ibx infra views

# List network views
ibx infra network-views
```

### Global Search

```bash
# Search by address
ibx search "10.0.0.5" --by address

# Search by FQDN
ibx search "www.example.com" --by fqdn

# Limit to specific type
ibx search "10.0.0.1" --type record:a
```

### Output Options (available on every query command)

```bash
# JSON output (pipe to jq)
ibx dns a --format json | jq '.[].name'

# CSV output
ibx dns a --format csv > records.csv

# Custom fields
ibx dns a --fields name,ipv4addr,comment

# Limit results
ibx dns a --limit 10

# Sort by field
ibx dhcp networks --sort network
```

### Config Management

```bash
# Show resolved config (password masked)
ibx config show

# Test connection
ibx --host 10.0.0.2 --username admin --password secret config test-connection

# Use a named profile
ibx --profile prod dns zones
```

## Supported WAPI Version

NIOS 9.0.8 -> WAPI v2.13.x

## Architecture

```
CLI (click) -> ObjectHandler -> QueryExecutor -> IbxClient -> infoblox_client -> WAPI
```

- **ObjectHandler**: Registry pattern - each NIOS object type has a handler class that defines default fields and translates CLI args to WAPI search filters
- **QueryExecutor**: Builds queries, applies pagination, handles server/client-side filtering
- **IbxClient**: Thin wrapper around `infoblox_client.connector.Connector`
- **Formatters**: table (Rich), json, csv
