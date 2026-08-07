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