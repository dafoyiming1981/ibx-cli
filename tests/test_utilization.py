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


def test_prometheus_formatter_empty_records():
    fmt = get_formatter("prometheus")
    output = fmt.render([], None)
    assert "# HELP" in output
    assert "# TYPE" in output


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
    assert "} 92.0\n" in output
    assert "} 126\n" in output
    used_line = [l for l in output.split("\n") if "ibx_network_used_ips" in l and "10.0.0.0/25" in l][0]
    assert "116" in used_line
