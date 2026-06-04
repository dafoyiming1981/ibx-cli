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
