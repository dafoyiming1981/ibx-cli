"""Tests for DNS zone-records Prometheus output."""


def _sample_dns_records():
    return [
        {"zone": "example.com", "type": "A", "count": 150, "view": "default"},
        {"zone": "example.com", "type": "AAAA", "count": 80, "view": "default"},
        {"zone": "example.com", "type": "CNAME", "count": 30, "view": "default"},
        {"zone": "example.com", "type": "MX", "count": 5, "view": "default"},
        {"zone": "example.com", "type": "NS", "count": 2, "view": "default"},
        {"zone": "example.com", "type": "TXT", "count": 12, "view": "default"},
    ]


def _build_prometheus_output(records):
    lines = [
        "# HELP ibx_dns_records_count Number of DNS records in the zone",
        "# TYPE ibx_dns_records_count gauge",
    ]
    for rec in records:
        label_set = f'zone="{rec["zone"]}"'
        if rec["view"]:
            label_set += f',view="{rec["view"]}"'
        label_set += f',type="{rec["type"]}"'
        lines.append(f'ibx_dns_records_count{{{label_set}}} {rec["count"]}')
    lines.append("")
    return "\n".join(lines)


def test_dns_prometheus_output_basic():
    output = _build_prometheus_output(_sample_dns_records())
    assert "ibx_dns_records_count" in output
    assert 'zone="example.com"' in output
    assert 'type="A"' in output
    assert "} 150\n" in output
    assert "# HELP" in output
    assert "# TYPE" in output


def test_dns_prometheus_output_multiple_zones():
    records = [
        {"zone": "example.com", "type": "A", "count": 150, "view": ""},
        {"zone": "lab.com", "type": "A", "count": 50, "view": ""},
    ]
    output = _build_prometheus_output(records)
    assert 'zone="example.com"' in output
    assert 'zone="lab.com"' in output
    assert "} 150\n" in output
    assert "} 50\n" in output


def test_dns_prometheus_output_empty():
    output = _build_prometheus_output([])
    assert "# HELP" in output
    assert "# TYPE" in output
