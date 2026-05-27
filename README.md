# ibx-cli

Infoblox NIOS CLI toolset for DNS/DHCP management via WAPI.

## 安装方法

按推荐程度排列，选最适合你环境的一种。

### 方法一: install_ibxcli.sh (推荐 — 适合 copy/paste 环境)

适用于无法直接执行 git clone 的受限环境（如 RHEL 8，只能通过 copy/paste 传代码）。

**步骤:**

1. 在构建主机上，复制脚本内容：
   ```bash
   cat dist/install_ibxcli.sh
   ```

2. 将脚本完整内容 copy/paste 到目标服务器，保存为 `install_ibxcli.sh`

3. 执行安装：
   ```bash
   bash install_ibxcli.sh
   ```

4. 添加别名到 `~/.bashrc`：
   ```bash
   echo 'alias ibx="$HOME/.local/bin/ibx"' >> ~/.bashrc
   source ~/.bashrc
   ```

5. 验证安装：
   ```bash
   ibx --version
   ```

安装路径: `~/.local/ibxcli/`（可通过 `IBX_INSTALL_DIR` 环境变量自定义）

**前置条件:**
- Python 3.12 已安装
- 可访问 pip 源（脚本内默认使用内部镜像，需修改 `your-internal-pip-mirror`）

### 方法二: git clone + pip install (推荐 — 有网络访问)

适用于可直接访问 GitHub 的环境。

```bash
cd /tmp
git clone https://github.com/dafoyiming1981/ibx-cli.git
cd ibx-cli
pip3.12 install --user -e .
```

验证：
```bash
ibx --version
```

### 方法三: venv + wheel (传统方式)

适用于需要隔离环境或离线安装的场景。

```bash
# 在构建主机上打包
cd ibx-cli
python3.12 -m pip wheel . -w dist/
tar czf ibx-cli.tar.gz ibx-cli/

# 传输到目标主机
scp ibx-cli.tar.gz user@target:/tmp/

# 在目标主机上安装
ssh user@target
cd /tmp && tar xzf ibx-cli.tar.gz
python3.12 -m venv ~/ibx-env
source ~/ibx-env/bin/activate
pip install /tmp/ibx-cli/dist/ibx_cli-0.1.0-py3-none-any.whl
```

### RHEL 8 安装 Python 3.9+

如果系统默认 Python 版本过低（RHEL 8 默认 3.6），需先升级：

```bash
sudo dnf module list python39
sudo dnf module install python39 -y
python3.9 --version
```

---

## 配置

### 快速开始

```bash
# 生成示例配置文件
ibx config init

# 编辑配置（填入 Infoblox 连接信息）
vi ~/.infoblox/config

# 保护配置文件（限制权限）
chmod 600 ~/.infoblox/config
```

### 配置文件格式 (~/.infoblox/config)

```yaml
defaults:
  host: 10.x.x.x             # Infoblox Grid Master IP 或 hostname
  username: admin             # API 用户名
  password: your_password     # API 密码
  wapi_version: "2.13"
  ssl_verify: false           # 自签名证书设为 false
  timeout: 30
  max_results: 1000

profiles:
  prod:
    host: infoblox-prod.example.com
    username: prod-admin
  lab:
    host: infoblox-lab.example.com
    username: lab-admin
    ssl_verify: false
```

### 环境变量 (可替代配置文件)

```bash
export IBX_HOST=10.x.x.x
export IBX_USERNAME=admin
export IBX_PASSWORD=your_password

# 直接运行命令，无需配置文件
ibx dns zones
```

### CLI 参数 (最高优先级)

```bash
ibx --host 10.0.0.2 --username admin --password secret dns zones
```

### 配置优先级

CLI 参数 > 环境变量 > 当前 profile > 配置文件 defaults > 硬编码默认值

---

## 使用指南

### 验证连接

```bash
ibx config test-connection
```

成功输出：
```
Connecting to 10.x.x.x...
Connected successfully!
  Grid: infoblox-grid
  WAPI version: 2.13
```

### DNS 命令

```bash
# 列出所有 A 记录
ibx dns a

# 按名称过滤 (支持 --regex)
ibx dns a --name "www.example.com"

# 在指定 zone 内搜索
ibx dns a --zone "srv.lab.ms.com.cn" --view "default"

# 列出 zone 内所有记录类型
ibx dns all-records --zone "example.com"

# 列出授权 zone
ibx dns zones --view "default"

# 列出主机记录
ibx dns hosts --name "server1"

# 其他记录类型
ibx dns cname --name "alias"
ibx dns mx --zone "example.com"
ibx dns txt --name "_dmarc"
ibx dns ptr --ipv4addr "10.0.0.1"
ibx dns aaaa --name "ipv6host"
ibx dns ns --zone "example.com"
```

### 支持的 DNS 记录类型

| 命令 | WAPI 对象 | 说明 | 支持的过滤参数 |
|------|-----------|------|----------------|
| `ibx dns zones` | `zone_auth` | 权威区域 | `--view`, `--fqdn`, `--regex` |
| `ibx dns a` | `record:a` | A 记录 (IPv4) | `--name`, `--ipv4addr`, `--zone`, `--view`, `--regex` |
| `ibx dns aaaa` | `record:aaaa` | AAAA 记录 (IPv6) | `--name`, `--ipv6addr`, `--zone`, `--view`, `--regex` |
| `ibx dns cname` | `record:cname` | CNAME 别名记录 | `--name`, `--canonical`, `--zone`, `--view`, `--regex` |
| `ibx dns mx` | `record:mx` | 邮件交换记录 | `--name`, `--zone`, `--view`, `--regex` |
| `ibx dns ns` | `record:ns` | 名称服务器记录 | `--name`, `--zone`, `--view`, `--regex` |
| `ibx dns txt` | `record:txt` | 文本记录 (SPF/DKIM 等) | `--name`, `--zone`, `--view`, `--regex` |
| `ibx dns ptr` | `record:ptr` | 反向解析记录 | `--name`, `--ipv4addr`, `--ipv6addr`, `--zone`, `--view`, `--regex` |
| `ibx dns hosts` | `record:host` | 主机记录 (含 IP+MAC) | `--name`, `--ipv4addr`, `--mac`, `--zone`, `--view`, `--regex` |
| `ibx dns all-records` | `allrecords` | 区域内所有记录聚合 | `--zone` (必填), `--view`, `--type` |

**说明:**

- `--regex` 标志可将 `--name` / `--fqdn` 参数从精确匹配切换为正则表达式匹配
- `all-records` 命令通过 `--type` 参数可过滤 WAPI 支持的任意记录类型（如 SRV、CAA、NAPTR 等），但这些类型暂无专用 CLI 命令
- 所有记录均支持 `--format`（json/csv/table）、`--fields`（自定义显示列）、`--limit`（限制结果数）等全局输出选项
- `EONID` 为自定义扩展属性（extensible attribute），已加入所有 DNS 记录的默认返回字段

### DHCP 命令

```bash
# 列出 IPv4 网络
ibx dhcp networks

# 按 CIDR 过滤
ibx dhcp networks --network "10.0.0.0/24"

# 按扩展属性 (extensible attributes) 过滤
ibx dhcp networks --vlan 100
ibx dhcp networks --vlan 100 --zone PROD --site BJ1

# OR 过滤 — 同时指定多个值，返回匹配任一值的结果
ibx dhcp networks --vlan 100 --vlan 200
ibx dhcp networks --site BJ1 --site SH1

# OR 过滤组合 — 多个维度产生笛卡尔积
ibx dhcp networks --vlan 100 --vlan 200 --site BJ1 --site SH1
# 等效于: (VLAN=100 OR VLAN=200) AND (Site=BJ1 OR Site=SH1)

# 带 ranges 树形视图
ibx dhcp networks --vlan 100 --with-ranges

# 列出固定地址 (DHCP reservation)
ibx dhcp fixed-address --mac "00:11:22:33:44:55"

# 列出 DHCP 租约
ibx dhcp leases --state active --limit 50

# 列出 IPv4 地址使用情况
ibx dhcp ipv4-addresses --network "10.0.0.0/24" --status used

# 列出 IPv6 网络
ibx dhcp ipv6-networks

# 列出网络容器
ibx dhcp containers
```

#### 支持的 extensible attributes 过滤

`ibx dhcp networks` 和 `ibx dhcp networks --with-ranges` 支持按以下扩展属性过滤：

| 参数 | WAPI Extensible Attribute | 说明 |
|------|--------------------------|------|
| `--vlan <值>` | `VLAN` | VLAN ID，支持重复指定多个值 (OR) |
| `--zone <值>` | `Zone` | 区域名称，支持重复指定多个值 (OR) |
| `--site <值>` | `Site` | 站点名称，支持重复指定多个值 (OR) |

**过滤逻辑：**

- 同一参数指定多个值 → **OR** 关系（如 `--vlan 100 --vlan 200` 匹配 VLAN=100 或 VLAN=200）
- 不同参数之间 → **AND** 关系（如 `--vlan 100 --site BJ1` 同时满足两个条件）
- 底层通过客户端多次查询并去重合并实现

### 基础设施命令

```bash
# 显示 Grid 属性
ibx infra grid

# 列出 Grid 成员
ibx infra members

# 列出 DNS 视图
ibx infra views

# 列出网络视图
ibx infra network-views
```

### 全局搜索

```bash
# 按地址搜索
ibx search "10.0.0.5" --by address

# 按 FQDN 搜索
ibx search "www.example.com" --by fqdn

# 限制搜索类型
ibx search "10.0.0.1" --type record:a
```

### 输出选项 (所有查询命令可用)

```bash
# JSON 输出 (可管道到 jq)
ibx dns a --format json | jq '.[].name'

# CSV 输出
ibx dns a --format csv > records.csv

# 自定义显示字段
ibx dns a --fields name,ipv4addr,comment

# 限制结果数量
ibx dns a --limit 10

# 按字段排序
ibx dhcp networks --sort network
```

### 配置管理

```bash
# 显示当前解析后的配置 (密码已掩码)
ibx config show

# 测试连接
ibx --host 10.0.0.2 --username admin --password secret config test-connection

# 使用命名 profile
ibx --profile prod dns zones
```

---

## 支持的 WAPI 版本

NIOS 9.0.8 → WAPI v2.13.x

## 架构

```
CLI (click) → ObjectHandler → QueryExecutor → IbxClient → infoblox_client → WAPI
```

- **ObjectHandler**: 注册表模式 — 每个 NIOS 对象类型有一个 handler 类，定义默认字段并将 CLI 参数翻译为 WAPI 搜索过滤器
- **QueryExecutor**: 构建查询、应用分页、处理服务端/客户端过滤和排序
- **IbxClient**: `infoblox_client.connector.Connector` 的轻量封装
- **Formatters**: table (Rich), json, csv
