# DNS Commands

DNS management commands for querying Infoblox DNS records via WAPI.

## `ibx dns zones`

List authoritative DNS zones.

| Option | Description |
|--------|-------------|
| `--view` | DNS view filter |
| `--fqdn` | Zone FQDN filter |
| `--regex` | Treat `--fqdn` as regex pattern |

```bash
ibx dns zones
ibx dns zones --view "default"
ibx dns zones --fqdn "example.com"
ibx dns zones --fqdn ".*\.example\.com" --regex
```

## `ibx dns a`

List DNS A (IPv4) records.

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--ipv4addr` | IPv4 address filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns a
ibx dns a --name "www.example.com"
ibx dns a --zone "srv.lab.ms.com.cn" --view "default"
ibx dns a --regex --name "www\..*\.example\.com"
```

## `ibx dns aaaa`

List DNS AAAA (IPv6) records.

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--ipv6addr` | IPv6 address filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns aaaa --name "ipv6host"
```

## `ibx dns cname`

List DNS CNAME alias records.

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--canonical` | Canonical name filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns cname --name "alias"
```

## `ibx dns mx`

List DNS MX (mail exchange) records.

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns mx --zone "example.com"
```

## `ibx dns ns`

List DNS NS (name server) records.

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns ns --zone "example.com"
```

## `ibx dns txt`

List DNS TXT records (SPF, DKIM, etc.).

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns txt --name "_dmarc"
```

## `ibx dns ptr`

List DNS PTR (reverse lookup) records.

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--ipv4addr` | IPv4 address filter |
| `--ipv6addr` | IPv6 address filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns ptr --ipv4addr "10.0.0.1"
```

## `ibx dns hosts`

List DNS host records (with IP + MAC).

| Option | Description |
|--------|-------------|
| `--name` | Record name filter |
| `--ipv4addr` | IPv4 address filter |
| `--mac` | MAC address filter |
| `--zone` | Zone filter |
| `--view` | DNS view filter |
| `--regex` | Treat `--name` as regex pattern |

```bash
ibx dns hosts --name "server1"
```

## `ibx dns all-records`

List all DNS records in a zone. **`--zone` is required.**

| Option | Description |
|--------|-------------|
| `--zone` | Zone (required) |
| `--view` | DNS view filter |
| `--type` | Filter by record type (SRV, CAA, NAPTR, etc.) |

```bash
ibx dns all-records --zone "example.com"
ibx dns all-records --zone "example.com" --type "SRV"
```

## `ibx dns zone-records`

Count DNS records per type in one or more zones, for Grafana/Prometheus dashboards. **`--zone` is required.**

| Option | Description |
|--------|-------------|
| `--zone` | Zone FQDN (repeatable, **required**) |
| `--view` | DNS view filter |
| `--format` | Output format: `prometheus` (default), `table`, `json`, `csv` |
| `--output` | Write output to file instead of stdout |
| `--shared` | Add `shared="true"` label to all metrics (for sharing dashboards across Grafana orgs) |

```bash
ibx dns zone-records --zone example.com
ibx dns zone-records --zone example.com --zone lab.com --output /var/lib/node_exporter/ibx_dns_records.prom
ibx dns zone-records --zone example.com --shared --output /var/lib/node_exporter/ibx_dns_records.prom
```

### Prometheus Output

```
# HELP ibx_dns_records_count Number of DNS records in the zone
# TYPE ibx_dns_records_count gauge
ibx_dns_records_count{zone="example.com",view="default",type="A"} 150
ibx_dns_records_count{zone="example.com",view="default",type="CNAME"} 30
```
