"""Tests for utilization export and Prometheus formatter."""

from ibxcli.formatters.base import get_formatter


def _sample_records():
    return [
        {"network": "10.0.0.0/24", "utilization": 730, "VLAN": "100", "Zone": "DC1", "Site": "BJ1", "members": "grid-master-01"},
        {"network": "10.0.1.0/16", "utilization": 450, "VLAN": "200", "Zone": "DC2", "Site": "SH1", "members": "grid-master-02"},
    ]


def test_prometheus_formatter_basic():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_records(), None)
    assert "ibx_network_utilization_percent" in output
    assert "ibx_network_total_ips" in output
    assert "ibx_network_used_ips" in output
    assert 'network="10.0.0.0/24"' in output
    assert 'vlan="100"' in output
    assert 'zone="DC1"' in output
    assert "} 73.0\n" in output


def test_prometheus_formatter_ip_counts():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_records(), None)
    assert "ibx_network_total_ips{network=\"10.0.0.0/24\"" in output
    lines = output.split("\n")
    used_line = [l for l in lines if "ibx_network_used_ips" in l and "10.0.0.0/24" in l][0]
    assert "185" in used_line


def test_prometheus_formatter_help_spacing():
    """HELP/TYPE should appear only once per metric, even with multiple records."""
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_records(), None)
    lines = output.split("\n")
    help_count = sum(1 for l in lines if l.startswith("# HELP ibx_network_utilization_percent"))
    type_count = sum(1 for l in lines if l.startswith("# TYPE ibx_network_utilization_percent"))
    assert help_count == 1, f"Expected 1 HELP for utilization_percent, got {help_count}"
    assert type_count == 1, f"Expected 1 TYPE for utilization_percent, got {type_count}"


def test_prometheus_formatter_empty_records():
    fmt = get_formatter("prometheus")
    output = fmt.render([], None)
    assert output == ""


def test_prometheus_formatter_no_vlan_zone():
    fmt = get_formatter("prometheus")
    records = [{"network": "10.0.0.0/24", "utilization": 500, "VLAN": "", "Zone": "", "Site": "", "members": ""}]
    output = fmt.render(records, None)
    assert 'network="10.0.0.0/24"' in output
    assert 'vlan=""' not in output


def test_prometheus_formatter_per_mille_to_percent():
    """WAPI returns utilization as per-mille (0-1000), should be converted to percent."""
    fmt = get_formatter("prometheus")
    records = [{"network": "10.0.0.0/25", "utilization": 920, "VLAN": "", "Zone": "", "Site": "", "members": ""}]
    output = fmt.render(records, None)
    util_line = [l for l in output.split("\n") if l.startswith("ibx_network_utilization_percent")][0]
    assert util_line.endswith("} 92.0")
    assert 'network="10.0.0.0/25"' in util_line
    assert "ibx_network_total_ips{network=\"10.0.0.0/25\"} 126" in output
    used_line = [l for l in output.split("\n") if "ibx_network_used_ips" in l and "10.0.0.0/25" in l][0]
    assert "116" in used_line


# ── Network EA labels: Auto-Provision / L2 / comment ──────────────

def test_network_ea_labels_on_utilization_metric():
    """Auto-Provision and L2 booleans normalize to true/false; comment is sanitized."""
    fmt = get_formatter("prometheus")
    records = [{
        "network": "10.0.0.0/24", "utilization": 500,
        "VLAN": "100", "Zone": "DC1", "Site": "BJ1", "members": "gm01",
        "Auto-Provision": "True", "L2": "False", "comment": 'uplink "A"\nsecond line',
    }]
    output = fmt.render(records, None)
    util_line = [l for l in output.split("\n") if l.startswith("ibx_network_utilization_percent")][0]
    assert 'auto_provision="true"' in util_line
    assert 'l2="false"' in util_line
    assert 'comment="uplink \\"A\\" second line"' in util_line


def test_network_ea_labels_default_false_when_missing():
    """Records without the EAs still emit auto_provision/l2 as false and empty comment."""
    fmt = get_formatter("prometheus")
    records = [{"network": "10.0.0.0/24", "utilization": 500, "VLAN": "", "Zone": "", "Site": "", "members": ""}]
    output = fmt.render(records, None)
    util_line = [l for l in output.split("\n") if l.startswith("ibx_network_utilization_percent")][0]
    assert 'auto_provision="false"' in util_line
    assert 'l2="false"' in util_line
    assert 'comment=""' in util_line


def test_network_ea_labels_only_on_utilization_metric():
    """total_ips / used_ips / next_available_ip must NOT carry the new labels (avoid series churn)."""
    fmt = get_formatter("prometheus")
    records = [{
        "network": "10.0.0.0/24", "utilization": 500,
        "VLAN": "", "Zone": "", "Site": "", "members": "",
        "Auto-Provision": "True", "L2": "True", "comment": "test",
        "next_available_ips": ["10.0.0.5", "10.0.0.6", "10.0.0.7"],
    }]
    output = fmt.render(records, None)
    for line in output.split("\n"):
        if line.startswith(("ibx_network_total_ips", "ibx_network_used_ips", "ibx_network_next_available_ip")):
            assert "auto_provision" not in line, f"unexpected label in: {line}"
            assert "comment" not in line, f"unexpected label in: {line}"
