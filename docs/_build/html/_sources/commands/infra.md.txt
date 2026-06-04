# Infrastructure Commands

Commands for querying Infoblox Grid infrastructure.

## `ibx infra grid`

Show grid properties.

```bash
ibx infra grid
```

## `ibx infra members`

List grid members with node-level HA status.

| Option | Description |
|--------|-------------|
| `--host-name` | Member hostname filter |
| `--service-state` | Service state filter |

```bash
ibx infra members
ibx infra members --host-name "grid-master"
```

Output shows each member with its nodes and HA status:

```
grid-master.example.com  platform: IB-4030
  Node 1  ha_status: active
  Node 2  ha_status: passive
```

## `ibx infra views`

List DNS views.

| Option | Description |
|--------|-------------|
| `--name` | DNS view name filter |
| `--network-view` | Associated network view filter |

```bash
ibx infra views
ibx infra views --name "default"
```

## `ibx infra network-views`

List network views.

| Option | Description |
|--------|-------------|
| `--name` | Network view name filter |

```bash
ibx infra network-views
```
