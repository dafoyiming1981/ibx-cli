# 固定 IP 地址 Grafana Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 扩展 `--format prometheus` 以输出固定 IP 指标，并新增一个展示当前固定 IP 的 Grafana dashboard。

**Architecture:** 复用现有 `--format prometheus` 通道和 node_exporter textfile collector。在 `PrometheusFormatter.render()` 中按记录是否含 `utilization` 字段区分 network 记录与 fixedaddress 记录；fixedaddress 每个 IP 输出一行 `ibx_fixedaddress{...} 1` 指标。新增 `grafana/dashboard-ibx-fixed-addresses.json`，单一 table 面板查询该指标。

**Tech Stack:** Python 3、click、node_exporter textfile、Prometheus、Grafana。

## Global Constraints

- 项目工作目录 `/Users/zhangyiming/ibx-cli/`
- 代码遵循 `src/ibxcli/` 布局，formatter 通过 `@register_formatter("prometheus")` 注册
- 复用现有 `_sanitize_label()` 转义 label 值；comment 换行替换为空格
- `# HELP` / `# TYPE` 行只输出一次（复用 `seen_metrics` 去重）
- 交付后重新生成 `dist/install_ibxcli.sh`，`git add` + `git commit` + `git push origin/main`
- 测试用 `pytest`

---

### Task 1: 扩展 PrometheusFormatter 输出固定 IP 指标

**Files:**
- Modify: `src/ibxcli/formatters/prometheus_fmt.py`
- Test: `tests/test_fixedaddress_formatter.py`（新建）

**Interfaces:**
- Consumes: `BaseFormatter.render(self, records: list[dict], fields: list[str] | None) -> str`、`_sanitize_label(value: str) -> str`（已存在）
- Produces: fixedaddress 记录输出 `ibx_fixedaddress{addr=...,mac=...,name=...,network=...,network_view=...,comment=...} 1` 指标。

- [ ] **Step 1: 写失败测试**

新建 `tests/test_fixedaddress_formatter.py`：

```python
"""Tests for fixed address Prometheus formatter output."""

from ibxcli.formatters.base import get_formatter


def _sample_fixedaddr():
    return [
        {
            "ipv4addr": "10.0.0.5",
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "web01",
            "network": "10.0.0.0/24",
            "network_view": "default",
            "comment": "nginx frontend",
        },
        {
            "ipv4addr": "10.0.1.10",
            "mac": "00:11:22:33:44:55",
            "name": "db01",
            "network": "10.0.1.0/24",
            "network_view": "default",
            "comment": "",
        },
    ]


def test_fixedaddress_prometheus_basic():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_fixedaddr(), None)
    assert "# HELP ibx_fixedaddress" in output
    assert "# TYPE ibx_fixedaddress gauge" in output
    assert 'ibx_fixedaddress{addr="10.0.0.5",mac="aa:bb:cc:dd:ee:ff",name="web01",network="10.0.0.0/24",network_view="default",comment="nginx frontend"} 1' in output
    assert 'ibx_fixedaddress{addr="10.0.1.10",mac="00:11:22:33:44:55",name="db01",network="10.0.1.0/24",network_view="default",comment=""} 1' in output


def test_fixedaddress_help_once():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_fixedaddr(), None)
    lines = output.split("\n")
    help_count = sum(1 for l in lines if l.startswith("# HELP ibx_fixedaddress"))
    type_count = sum(1 for l in lines if l.startswith("# TYPE ibx_fixedaddress"))
    assert help_count == 1
    assert type_count == 1


def test_fixedaddress_comment_escaping():
    fmt = get_formatter("prometheus")
    records = [{
        "ipv4addr": "10.0.0.9", "mac": "aa:bb:cc", "name": "",
        "network": "10.0.0.0/24", "network_view": "",
        "comment": 'quoted "x" back\\slash newline\nhere',
    }]
    output = fmt.render(records, None)
    # 引号、反斜杠被转义；换行被替换为空格
    assert output.count(chr(10)) <= 4  # 帮助行+类型行+末尾空行+数据行，无额外换行注入
    assert "quoted \\\"x\\\" back\\\\slash newline here" in output


def test_fixedaddress_missing_fields_empty():
    fmt = get_formatter("prometheus")
    records = [{"ipv4addr": "10.0.0.1"}]
    output = fmt.render(records, None)
    assert 'ibx_fixedaddress{addr="10.0.0.1",mac="",name="",network="",network_view="",comment=""} 1' in output


def test_network_records_still_work():
    """现有 network 记录输出不受影响。"""
    fmt = get_formatter("prometheus")
    records = [{"network": "10.0.0.0/24", "utilization": 500, "VLAN": "", "Zone": "", "Site": "", "members": ""}]
    output = fmt.render(records, None)
    assert "ibx_network_utilization_percent" in output
    assert "ibx_fixedaddress" not in output
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_fixedaddress_formatter.py -v`
Expected: FAIL（`ibx_fixedaddress` 未输出，断言失败）

- [ ] **Step 3: 写最小实现**

在 `src/ibxcli/formatters/prometheus_fmt.py` 中，`render()` 内对每条记录判断：若记录含 `utilization` 字段则走现有 network 逻辑；否则走 fixedaddress 逻辑。

修改 `render` 使 network 处理仅在记录含 `utilization` 时执行：

```python
def render(self, records: list[dict], fields: list[str] | None) -> str:
    lines: list[str] = []
    seen_metrics: set[str] = set()

    for rec in records:
        # fixedaddress 记录：无 utilization 字段
        if "utilization" not in rec:
            self._render_fixedaddress(rec, lines, seen_metrics)
            continue

        network = rec.get("network", "")
        # ... 现有 network 逻辑保持不变 ...
```

新增私有方法：

```python
def _render_fixedaddress(self, rec: dict, lines: list[str], seen_metrics: set[str]) -> None:
    def _clean(v):
        return _sanitize_label((v or "").replace("\n", " "))

    if "ibx_fixedaddress" not in seen_metrics:
        lines.append("# HELP ibx_fixedaddress Fixed IP address reservations")
        lines.append("# TYPE ibx_fixedaddress gauge")
        seen_metrics.add("ibx_fixedaddress")

    lbl = (
        f'addr="{_clean(rec.get("ipv4addr"))}",'
        f'mac="{_clean(rec.get("mac"))}",'
        f'name="{_clean(rec.get("name"))}",'
        f'network="{_clean(rec.get("network"))}",'
        f'network_view="{_clean(rec.get("network_view"))}",'
        f'comment="{_clean(rec.get("comment"))}"'
    )
    lines.append(f"ibx_fixedaddress{{{lbl}}} 1")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_fixedaddress_formatter.py -v`
Expected: PASS（6 个测试全过）

- [ ] **Step 5: 运行全量测试确认无回归**

Run: `pytest -v`
Expected: 全部 PASS（含现有 `test_utilization.py`）

- [ ] **Step 6: 提交**

```bash
git add src/ibxcli/formatters/prometheus_fmt.py tests/test_fixedaddress_formatter.py
git commit -m "feat: export fixed address metrics in prometheus format"
```

---

### Task 2: 新增固定 IP Grafana dashboard JSON

**Files:**
- Create: `grafana/dashboard-ibx-fixed-addresses.json`

**Interfaces:**
- Consumes: Task 1 产出的 `ibx_fixedaddress` 指标（label: addr, mac, name, network, network_view, comment）
- Produces: 可导入 Grafana 的 dashboard JSON，单一 table 面板

- [ ] **Step 1: 创建 dashboard JSON**

创建 `grafana/dashboard-ibx-fixed-addresses.json`：

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "links": [],
  "panels": [
    {
      "id": 1,
      "title": "Fixed IP Addresses",
      "type": "table",
      "gridPos": {
        "h": 14,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "targets": [
        {
          "datasource": {
            "type": "prometheus"
          },
          "expr": "ibx_fixedaddress",
          "instant": true,
          "format": "table"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "align": "auto",
            "cellOptions": {
              "type": "auto"
            }
          }
        },
        "overrides": []
      },
      "transformations": [
        {
          "id": "organize",
          "options": {
            "excludeByName": {
              "Time": true,
              "__name__": true,
              "job": true,
              "instance": true,
              "Value": true
            },
            "renameByName": {
              "addr": "IP Address",
              "mac": "MAC",
              "name": "Name",
              "network": "Network",
              "network_view": "View",
              "comment": "Comment"
            }
          }
        }
      ]
    }
  ],
  "schemaVersion": 39,
  "tags": ["infoblox", "dhcp", "fixed-address"],
  "templating": {
    "list": [
      {
        "name": "network_view",
        "type": "query",
        "datasource": {
          "type": "prometheus"
        },
        "query": "label_values(ibx_fixedaddress, network_view)",
        "refresh": 2,
        "multi": true,
        "includeAll": true,
        "label": "View"
      }
    ]
  },
  "time": {
    "from": "now-24h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "Infoblox Fixed IP Addresses",
  "uid": "ibx-fixed-addresses",
  "version": 1
}
```

- [ ] **Step 2: 验证 JSON 合法且结构正确**

Run: `python3 -c "import json;d=json.load(open('grafana/dashboard-ibx-fixed-addresses.json'));assert d['panels'][0]['type']=='table';assert d['panels'][0]['targets'][0]['expr']=='ibx_fixedaddress';assert d['panels'][0]['transformations'][0]['options']['renameByName']['addr']=='IP Address';print('OK')"`
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add grafana/dashboard-ibx-fixed-addresses.json
git commit -m "feat: add fixed IP addresses Grafana dashboard"
```

---

### Task 3: 重新生成安装脚本并推送

**Files:**
- Modify: `dist/install_ibxcli.sh`（由 `python3 dist/gen_installer.py` 生成）

**Interfaces:**
- Consumes: 前面所有改动
- Produces: 更新后的安装脚本 + 推送 remote

- [ ] **Step 1: 重新生成安装脚本**

Run: `python3 dist/gen_installer.py`
Expected: `dist/install_ibxcli.sh` 内容更新（无报错）

- [ ] **Step 2: 提交安装脚本**

```bash
git add dist/install_ibxcli.sh
git commit -m "Regenerate install_ibxcli.sh with fixed address prometheus export"
```

- [ ] **Step 3: 推送**

```bash
git push origin main
```

Expected: 推送成功，remote `origin/main` 领先于本地无差异。

---

## Self-Review 记录

**Spec 覆盖：**
- 扩展 `PrometheusFormatter` 输出固定 IP 指标 → Task 1
- 新增 dashboard JSON 单一 table 面板 → Task 2
- comment 作为 label、换行转空格 → Task 1 Step 1 测试 + Step 3 实现
- 缺失字段置空 → Task 1 `test_fixedaddress_missing_fields_empty`
- HELP/TYPE 仅一次 → Task 1 `test_fixedaddress_help_once`
- 现有 network 记录不回归 → Task 1 `test_network_records_still_work` + Step 5 全量测试
- 重新生成安装脚本 + 提交推送 → Task 3

**占位符扫描：** 无 TBD/TODO，所有步骤含实际代码。

**类型一致性：** `_render_fixedaddress(rec, lines, seen_metrics)` 签名在 Step 3 定义，测试中使用的指标名 `ibx_fixedaddress` 与 label 名（addr/mac/name/network/network_view/comment）在 Task 1 和 Task 2 一致。