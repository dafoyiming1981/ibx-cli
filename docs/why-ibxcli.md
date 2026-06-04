# Why ibx-cli

ibx-cli is a command-line tool built for COD teams to manage Infoblox NIOS DNS/DHCP infrastructure. It interacts directly with the Infoblox Grid via WAPI, compressing operations that would take multiple GUI clicks into a single command with flat, actionable output.

## Why do we need ibx-cli?

### Pain Point 1: Tree-style GUI navigation makes lookup inefficient

In the Infoblox web interface, information is organized in a **hierarchical tree**:

```
IPAM → Network View → 10.0.0.0/8 → 10.10.0.0/16 → 10.10.5.0/24 → Ranges
  ↓
DNS → Zone Auth → example.com → Records → Next Page → Next Page
  ↓
Network Services → DHCP → Leases → Filter → Next Page
```

To answer "Which networks are under VLAN 200? What DHCP ranges does each one have?", you would:

1. Open the IPAM view
2. Select the Network View
3. Expand the network hierarchy
4. Click into each subnet
5. Check extensible attributes on each subnet
6. Click into the Ranges tab
7. Go back, repeat steps 4-6
8. Manually compare findings in the browser

**With ibx-cli:**

```bash
ibx dhcp networks --vlan 200 --with-ranges
```

A single command produces the full tree view — networks with their ranges nested underneath, each annotated with failover association, DDNS status, and VLAN/Zone/Site attributes. Output goes straight to the terminal and can be piped to `grep`, `less`, or `jq`.

### Pain Point 2: Configuration extraction and diffing is difficult

Day-to-day operations often require comparing configurations across environments or before/after changes:

- "What's different between Prod and Lab DNS zone configs?"
- "Which DHCP range failover settings changed after this deployment?"
- "Snapshot all grid member HA states before the upgrade."

**GUI approach:** Screenshot each page or transcribe manually, then compare in Excel.

**ibx-cli approach:**

```bash
# Export prod environment network config
ibx --profile prod dhcp networks --format json > prod-networks.json

# Export lab environment network config
ibx --profile lab dhcp networks --format json > lab-networks.json

# Diff them directly
diff <(jq . prod-networks.json) <(jq . lab-networks.json)
```

JSON/CSV output formats enable version-controlled configs, automated auditing, and CI/CD pipeline integration.

### Pain Point 3: No quick status checks for upgrades and maintenance

Before upgrading a Grid Member, operators need to confirm:

- What is the current HA state? Which node is active, which is passive?
- Which network ranges rely on failover? Will the upgrade impact DHCP service?
- Is DNS resolution working correctly after the change?

**GUI approach:** Check each member in Grid → Members page individually, then switch to the Network page to verify range associations.

**ibx-cli approach:**

```bash
# See all member HA states at a glance
ibx infra members

# Example output:
# grid-master.example.com  platform: IB-4030
#   Node 1  ha_status: active
#   Node 2  ha_status: passive

# Check range and failover associations for a VLAN
ibx dhcp networks --vlan 200 --with-ranges

# Capture before/after state and diff
ibx dns a --name "app.example.com" --format json > before.json
# ... perform the change ...
ibx dns a --name "app.example.com" --format json > after.json
diff <(jq . before.json) <(jq . after.json)
```

## Real-World Scenarios

### Scenario 1: A colleague asks about VLAN assignments

> "Can you check what networks are configured for VLAN 200?"

```bash
ibx dhcp networks --vlan 200
```

Output includes network CIDR, comments, and custom attributes like VLAN, Zone, and Site — all in one flat view.

```bash
# Need to see DHCP ranges under those networks too?
ibx dhcp networks --vlan 200 --with-ranges
```

### Scenario 2: Quickly locate DNS records and verify changes

> "Has the A record for app-v2.example.com been updated?"

```bash
# Before the change
ibx dns a --name "app-v2.example.com"

# After the change
ibx dns a --name "app-v2.example.com"

# Not sure of the exact name? Use regex
ibx dns a --regex --name "app.*example\.com"
```

### Scenario 3: Pre-upgrade HA health check

```bash
# Confirm HA roles for all members
ibx infra members

# Check which ranges depend on failover
ibx dhcp networks --with-ranges | grep -i failover

# Verify current Grid version
ibx infra grid
```

## ibx-cli vs Infoblox GUI

| Dimension | Infoblox GUI | ibx-cli |
|-----------|-------------|---------|
| Navigation | Tree hierarchy, multi-page jumps | Flat output, single command |
| Filtering | Fixed forms, limited combinations | Arbitrary parameter combos, OR/AND logic |
| Batch ops | Page-by-page manual review | Pipe to grep/jq/awk |
| Config export | Screenshots or manual notes | Direct JSON/CSV output |
| Diffing | Excel or visual comparison | Automated with `diff`, `git diff` |
| Automation | No integration path | Scriptable, CI/CD-ready |
| Learning curve | Requires familiarity with UI layout | Familiar CLI experience |

## Architecture

```
CLI (click) → ObjectHandler → QueryExecutor → IbxClient → infoblox_client → WAPI
```

- **ObjectHandler**: Registry pattern — each NIOS object type has a handler class that translates CLI arguments into WAPI search filters
- **QueryExecutor**: Builds queries, handles pagination, applies server-side and client-side filtering and sorting
- **IbxClient**: Lightweight wrapper around the infoblox-client SDK
- **Formatters**: table (Rich), JSON, CSV output formats
