# Search Command

Global cross-object search.

## `ibx search`

Search across all DNS record objects by address, FQDN, or MAC address.

```bash
ibx search "10.0.0.5" --by address
ibx search "www.example.com" --by fqdn
ibx search "10.0.0.1" --type record:a
```

| Option | Description |
|--------|-------------|
| `QUERY` | Search string (positional argument) |
| `--by` | Search field: `address`, `fqdn`, or `mac_address` (default: `address`) |
| `--type` | Limit search to object type (e.g., `record:a`, `network`) |
| `--format` | Output format: `table`, `json`, `csv` |
| `--fields` | Comma-separated fields to display |
| `--limit` | Max rows to display (default: 100) |
| `--sort` | Sort results by field |

By default, `ibx search` queries the following record types: `record:a`, `record:aaaa`, `record:cname`, `record:host`, `record:ptr`, `record:txt`. Results are merged and displayed together with an `_obj_type` column indicating the source object type.
