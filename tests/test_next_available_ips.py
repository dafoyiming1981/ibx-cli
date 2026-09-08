"""Tests for next-3-available-IP resolution and Prometheus info metric.

Covers:
1. QueryExecutor: next_available_ip called with num=3, list field padded
   with "No available IP", singular field = first IP, _ref stripped,
   refs stay aligned after sort/limit.
2. PrometheusFormatter: ibx_network_next_available_ip info metric with
   ip1/ip2/ip3 labels, --shared support, backward compatibility.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ibxcli.core.query import QueryExecutor
from ibxcli.formatters.base import get_formatter
from ibxcli.objects.dhcp import NetworkHandler


# ── Fake WAPI data ────────────────────────────────────────────────

def _fake_network(cidr: str, util: int, vlan: str = "100") -> dict:
    return {
        "_ref": f"network/{cidr}/default",
        "network": cidr,
        "utilization": util,
        "members": [{"name": "gm01.example.com"}],
        "extattrs": {
            "VLAN": {"value": vlan},
            "Zone": {"value": "DC1"},
            "Site": {"value": "BJ1"},
        },
    }


def _executor_with_ips(mock_client, records, ips_by_ref):
    """Configure mock: get() returns records, call_func() returns IPs per ref."""
    mock_client.get.return_value = records

    def fake_call_func(func_name, ref, payload=None):
        assert func_name == "next_available_ip"
        assert payload == {"num": 3}, f"expected num=3, got {payload}"
        if ref not in ips_by_ref:
            raise Exception("Network has no available IPs")
        return {"ips": [{"ip": ip} for ip in ips_by_ref[ref]]}

    mock_client.call_func.side_effect = fake_call_func
    return QueryExecutor(mock_client)


def _run(executor, filters=None, limit=None, sort_by=None):
    handler = NetworkHandler()
    params = executor.build_params(
        obj_type=handler.obj_type,
        search_filters=filters or {},
        default_fields=handler.default_return_fields,
    )
    params.limit = limit
    params.sort_by = sort_by
    return executor.execute(params)


# ── Executor: IP resolution ───────────────────────────────────────

@pytest.fixture
def mock_client():
    return MagicMock()


def test_num_3_requested_and_list_populated(mock_client):
    records = [_fake_network("10.0.0.0/24", 500)]
    executor = _executor_with_ips(mock_client, records, {
        "network/10.0.0.0/24/default": ["10.0.0.57", "10.0.0.58", "10.0.0.59"],
    })
    result = _run(executor)
    rec = result.records[0]
    assert rec["next_available_ips"] == ["10.0.0.57", "10.0.0.58", "10.0.0.59"]
    assert rec["next_available_ipv4address"] == "10.0.0.57"
    assert "_ref" not in rec


def test_partial_availability_padded(mock_client):
    """WAPI returns fewer than 3 IPs → pad with 'No available IP'."""
    records = [_fake_network("10.0.0.0/24", 990)]
    executor = _executor_with_ips(mock_client, records, {
        "network/10.0.0.0/24/default": ["10.0.0.254"],
    })
    result = _run(executor)
    assert result.records[0]["next_available_ips"] == [
        "10.0.0.254", "No available IP", "No available IP"]
    assert result.records[0]["next_available_ipv4address"] == "10.0.0.254"


def test_full_network_all_no_available_ip(mock_client):
    """100% utilized → WAPI errors → all three positions 'No available IP'."""
    records = [_fake_network("10.0.0.0/24", 1000)]
    executor = _executor_with_ips(mock_client, records, {})  # ref missing → raises
    result = _run(executor)
    assert result.records[0]["next_available_ips"] == ["No available IP"] * 3
    assert result.records[0]["next_available_ipv4address"] == "No available IP"


def test_limit_no_index_error_and_calls_capped(mock_client):
    """--limit smaller than record count must not crash; only limited refs resolved."""
    records = [_fake_network(f"10.0.{i}.0/24", 500) for i in range(5)]
    ips = {f"network/10.0.{i}.0/24/default": [f"10.0.{i}.10"] for i in range(5)}
    executor = _executor_with_ips(mock_client, records, ips)
    result = _run(executor, limit=2)
    assert len(result.records) == 2
    assert mock_client.call_func.call_count == 2


def test_sort_keeps_ips_aligned(mock_client):
    """After sorting, each record must carry ITS OWN next available IPs."""
    records = [
        _fake_network("10.0.2.0/24", 500),
        _fake_network("10.0.1.0/24", 500),
    ]
    ips = {
        "network/10.0.1.0/24/default": ["10.0.1.10", "10.0.1.11", "10.0.1.12"],
        "network/10.0.2.0/24/default": ["10.0.2.10", "10.0.2.11", "10.0.2.12"],
    }
    executor = _executor_with_ips(mock_client, records, ips)
    result = _run(executor, sort_by="network")
    assert result.records[0]["network"] == "10.0.1.0/24"
    assert result.records[0]["next_available_ips"][0] == "10.0.1.10"
    assert result.records[1]["network"] == "10.0.2.0/24"
    assert result.records[1]["next_available_ips"][0] == "10.0.2.10"


# ── Formatter: info metric ────────────────────────────────────────

def _fmt_record(next_ips=None, **extra):
    rec = {"network": "10.0.0.0/24", "utilization": 730, "VLAN": "100",
           "Zone": "DC1", "Site": "BJ1", "members": "gm01"}
    if next_ips is not None:
        rec["next_available_ips"] = next_ips
    rec.update(extra)
    return rec


def test_info_metric_rendered():
    fmt = get_formatter("prometheus")
    output = fmt.render(
        [_fmt_record(["10.0.0.57", "10.0.0.58", "10.0.0.59"])], None)
    line = [l for l in output.split("\n")
            if l.startswith("ibx_network_next_available_ip{")][0]
    assert 'network="10.0.0.0/24"' in line
    assert 'ip1="10.0.0.57"' in line
    assert 'ip2="10.0.0.58"' in line
    assert 'ip3="10.0.0.59"' in line
    assert line.endswith("} 1")


def test_info_metric_no_available_ip():
    fmt = get_formatter("prometheus")
    output = fmt.render(
        [_fmt_record(["No available IP"] * 3)], None)
    line = [l for l in output.split("\n")
            if l.startswith("ibx_network_next_available_ip{")][0]
    assert line.count("No available IP") == 3


def test_info_metric_shared_label():
    fmt = get_formatter("prometheus")
    output = fmt.render(
        [_fmt_record(["10.0.0.57", "10.0.0.58", "10.0.0.59"])], None, shared=True)
    line = [l for l in output.split("\n")
            if l.startswith("ibx_network_next_available_ip{")][0]
    assert 'shared="true"' in line


def test_info_metric_absent_without_field():
    """Records lacking next_available_ips (old callers) → no info metric emitted."""
    fmt = get_formatter("prometheus")
    output = fmt.render([_fmt_record()], None)
    assert "ibx_network_next_available_ip" not in output
    # existing metrics unaffected
    assert "ibx_network_utilization_percent" in output


def test_info_metric_help_once():
    fmt = get_formatter("prometheus")
    output = fmt.render([
        _fmt_record(["10.0.0.57", "10.0.0.58", "10.0.0.59"]),
        _fmt_record(["10.0.1.57", "10.0.1.58", "10.0.1.59"], network="10.0.1.0/24"),
    ], None)
    lines = output.split("\n")
    assert sum(1 for l in lines
               if l.startswith("# HELP ibx_network_next_available_ip")) == 1
    assert sum(1 for l in lines
               if l.startswith("# TYPE ibx_network_next_available_ip")) == 1
