# DHCP Commands

DHCP management commands for querying Infoblox networks, ranges, leases, and fixed addresses.

## `ibx dhcp networks`

List IPv4 networks. Supports extensible attribute filtering and range tree view.

| Option | Description |
|--------|-------------|
| `--network` | CIDR network filter (e.g., `10.0.0.0/24`) |
| `--network-view` | Network view filter |
| `--with-ranges` | Show DHCP ranges under each network in tree view |
| `--vlan` | VLAN filter (repeatable, OR logic) |
| `--zone` | Zone filter (repeatable, OR logic) |
| `--site` | Site filter (repeatable, OR logic) |

```bash
ibx dhcp networks
ibx dhcp networks --network "10.0.0.0/24"
ibx dhcp networks --vlan 100
ibx dhcp networks --vlan 100 --vlan 200 --site BJ1 --site SH1
ibx dhcp networks --vlan 100 --with-ranges
```

### Filtering Logic

- Same parameter with multiple values: **OR** (`--vlan 100 --vlan 200` matches VLAN=100 or 200)
- Different parameters: **AND** (`--vlan 100 --site BJ1` requires both)
- Underlying implementation performs multiple WAPI queries with client-side deduplication

### Tree View (`--with-ranges`)

Shows each network with its DHCP ranges nested underneath, including failover association, DDNS status, and extensible attributes:

```
10.0.0.0/24  Site: BJ1
  10.0.0.100 - 10.0.0.200  FAILOVER  my-failover-group  DDNS: ON  (example.com)
  10.0.0.201 - 10.0.0.250  MEMBER  member1.example.com
```

## `ibx dhcp ipv6-networks`

List IPv6 networks.

| Option | Description |
|--------|-------------|
| `--network` | CIDR IPv6 network filter |
| `--network-view` | Network view filter |

```bash
ibx dhcp ipv6-networks
```

## `ibx dhcp containers`

List network containers.

| Option | Description |
|--------|-------------|
| `--network` | CIDR container network filter |
| `--network-view` | Network view filter |

```bash
ibx dhcp containers
```

## `ibx dhcp fixed-address`

List DHCP fixed addresses (reservations).

| Option | Description |
|--------|-------------|
| `--ipv4addr` | IPv4 address filter |
| `--mac` | MAC address filter |
| `--network-view` | Network view filter |

```bash
ibx dhcp fixed-address --mac "00:11:22:33:44:55"
```

## `ibx dhcp ipv4-addresses`

List IPv4 address usage status.

| Option | Description |
|--------|-------------|
| `--network` | CIDR network filter |
| `--status` | Lease status filter (e.g., `used`, `free`) |
| `--mac` | MAC address filter |
| `--name` | Client name filter |

```bash
ibx dhcp ipv4-addresses --network "10.0.0.0/24" --status used
```

## `ibx dhcp ranges`

List DHCP address ranges. Supports extensible attribute filtering.

| Option | Description |
|--------|-------------|
| `--network` | CIDR network filter |
| `--network-view` | Network view filter |
| `--vlan` | VLAN filter (repeatable, OR logic) |
| `--zone` | Zone filter (repeatable, OR logic) |
| `--site` | Site filter (repeatable, OR logic) |

```bash
ibx dhcp ranges
ibx dhcp ranges --vlan 100
ibx dhcp ranges --vlan 100 --vlan 200 --zone PROD
```

:::{note}
WAPI doesn't support extensible attribute search on range objects directly. This command resolves matching networks by EA, then filters ranges by CIDR.
:::

## `ibx dhcp leases`

List DHCP leases.

| Option | Description |
|--------|-------------|
| `--network` | CIDR network filter |
| `--network-view` | Network view filter |

```bash
ibx dhcp leases --state active --limit 50
```

## `ibx dhcp utilization`

Export network utilization metrics for Grafana/Prometheus dashboards. Queries networks filtered by VLAN and Zone, outputs utilization percentage (integer 0-100), total IPs, and used IPs.

| Option | Description |
|--------|-------------|
| `--vlan` | VLAN filter (repeatable, **required**) |
| `--zone` | Zone filter (repeatable, **required**) |
| `--format` | Output format: `prometheus` (default), `table`, `json`, `csv` |
| `--output` | Write output to file instead of stdout |
| `--limit` | Max networks to query (default: all) |
| `--shared` | Add `shared="true"` label to all metrics (for sharing dashboards across Grafana orgs) |

```bash
ibx dhcp utilization --vlan 100 --zone DC1
ibx dhcp utilization --vlan 100 --vlan 200 --zone DC1 --zone DC2 --format prometheus
ibx dhcp utilization --vlan 100 --zone DC1 --format prometheus --output /var/lib/node_exporter/ibx_utilization.prom
ibx dhcp utilization --vlan 100 --zone DC1 --shared --output /var/lib/node_exporter/ibx_utilization.prom
```

### Prometheus Output

```
# HELP ibx_network_utilization_percent Network utilization percentage (0-100)
# TYPE ibx_network_utilization_percent gauge
ibx_network_utilization_percent{network="10.0.0.0/24",vlan="100",zone="DC1"} 73
# HELP ibx_network_next_available_ip Next 3 available IP addresses in the network
# TYPE ibx_network_next_available_ip gauge
ibx_network_next_available_ip{network="10.0.0.0/24",vlan="100",zone="DC1",ip1="10.0.0.57",ip2="10.0.0.58",ip3="10.0.0.59"} 1
ibx_network_total_ips{network="10.0.0.0/24",vlan="100",zone="DC1"} 254
ibx_network_used_ips{network="10.0.0.0/24",vlan="100",zone="DC1"} 185
```

`ibx_network_next_available_ip` is an info metric (value always `1`); the IP
addresses are carried in the `ip1`/`ip2`/`ip3` labels. When a network is 100%
utilized (or has fewer than 3 IPs left), the remaining positions show
`No available IP`. In Grafana, query it with **Instant** + **Format as Table**
and join with `ibx_network_utilization_percent` on the `network` label.

### Cron Usage

```
0 2 * * * ibx dhcp utilization --vlan 100 --vlan 200 --zone DC1 --format prometheus --output /var/lib/node_exporter/ibx_utilization.prom
```

### Cron Environment Note

When running under cron, the CLI automatically loads `IBX_*` environment variables from `~/.bashrc` if they are not already present in the cron environment. This means you do **not** need to add `source ~/.bashrc` to your cron job — just ensure the relevant `export IBX_*=...` lines exist in `~/.bashrc`.
