# 固定 IP 地址 Grafana Dashboard — 设计文档

日期：2026-08-07
状态：已批准

## 目标

为 ibx-cli 新增一个展示当前固定 IP 地址（fixedaddress）的 Grafana dashboard，并扩展 `--format prometheus` 输出以支持 fixedaddress 对象。

## 范围

**本次包含：**
- 扩展 `PrometheusFormatter` 以输出固定 IP 指标
- 新增 Grafana dashboard JSON（单一 table 面板）

**本次不包含（后续再做）：**
- 过去 7 天新增/清理的固定 IP 列表（历史事件数据）。fixedaddress 对象无时间戳，需引入数据源/快照对比方案，另行设计。

## 架构

```
ibx dhcp fixed-addresses --format prometheus
        │  (新增 fixedaddress 分支)
        ▼
PrometheusFormatter.render()  ──►  ibx_fixedaddress{...} 1  每 IP 一行
        │
        ▼  (node_exporter textfile collector，外部已有通道)
   Prometheus ──► Grafana dashboard-ibx-fixed-addresses.json
```

数据采集通道复用现有 network utilization 的机制（node_exporter textfile collector，配置在项目外）。

### 采集命令与 textfile 命名

`--output` 参数已加入通用 `@output_options`，所有查询命令（含 `fixed-addresses`）都支持直接写文件：

```bash
ibx dhcp fixed-addresses --format prometheus --output /var/lib/node_exporter/ibx_fixedaddress.prom
```

cron 示例（每天 3 点采集一次）：

```bash
0 3 * * * ibx dhcp fixed-addresses --format prometheus --output /var/lib/node_exporter/ibx_fixedaddress.prom
```

`.prom` 文件名遵循现有 `ibx_utilization.prom` 的 `ibx_<对象>.prom` 命名风格。

## 组件改动

### 1. `src/ibxcli/formatters/prometheus_fmt.py`

在 `PrometheusFormatter.render()` 中，按记录是否含 `utilization` 字段区分 network 记录 vs fixedaddress 记录：

- **network 记录**（含 `utilization`）：现有逻辑不变
- **fixedaddress 记录**（不含 `utilization`）：输出指标

输出格式：
```
# HELP ibx_fixedaddress Fixed IP address reservations
# TYPE ibx_fixedaddress gauge
ibx_fixedaddress{addr="10.0.0.5",mac="aa:bb:cc:dd:ee:ff",name="web01",network="10.0.0.0/24",network_view="default",comment="nginx frontend"} 1
```

规则：
- 每个固定 IP 一行，value=1，字段作为 label
- label 集合：`addr`, `mac`, `name`, `network`, `network_view`, `comment`
- 复用现有 `_sanitize_label()` 转义（引号、反斜杠）；缺失字段置空字符串
- comment 中换行替换为空格（Prometheus label 值不允许换行）
- `# HELP` / `# TYPE` 行只输出一次（复用现有 `seen_metrics` 去重机制）

### 2. `grafana/dashboard-ibx-fixed-addresses.json`

- 单一 table 面板
- 列：addr / mac / name / network / network_view / comment
- 数据源：prometheus
- 查询：`ibx_fixedaddress`，instant 查询
- schema 结构参照现有 `dashboard-ibx-network-utilization.json`

## 错误处理

- 无固定 IP 时：不产生 `ibx_fixedaddress` 指标，Grafana 表格显示空/无数据
- label 值转义失败不致崩溃（`_sanitize_label` 兜底）

## 测试

- 单元测试 `PrometheusFormatter`：
  - 输入 fixedaddress 记录 → 断言输出行格式正确
  - comment 含特殊字符（引号、反斜杠、换行）→ 断言正确转义
  - 缺失字段 → 断言置空
- 现有 network 记录测试不回归

## 数据量考量

当前环境固定 IP < 500，Prometheus 每 IP 一行（label 基数）无压力。

## 交付后动作

按记忆中的 ibx-cli 工作流：
1. 重新生成 `dist/install_ibxcli.sh`（`python3 dist/gen_installer.py`）
2. `git add` + `git commit`（源码 + installer + dashboard）
3. `git push` 到 `origin/main`