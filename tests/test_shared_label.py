"""Tests for the --shared flag: adds shared="true" label to Prometheus output.

Purpose: allow the same dashboard to be shared across multiple Grafana orgs,
each org filtering on the shared label.
"""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from ibxcli.core.query import QueryResult
from ibxcli.formatters.base import get_formatter
from ibxcli.formatters.prometheus_fmt import render_dns_prometheus


def _sample_network_records():
    return [
        {"network": "10.0.0.0/24", "utilization": 730, "VLAN": "100",
         "Zone": "DC1", "Site": "BJ1", "members": "gm01"},
    ]


def _sample_fixedaddr_records():
    return [
        {"ipv4addr": "10.0.0.5", "mac": "aa:bb:cc:dd:ee:ff", "name": "web01",
         "network": "10.0.0.0/24", "network_view": "default", "comment": ""},
    ]


def _sample_dns_counts():
    return [
        {"zone": "example.com", "type": "A", "count": 150, "view": "default"},
    ]


# ── Formatter: network utilization metrics ────────────────────────

def test_network_metrics_include_shared_label():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_network_records(), None, shared=True)
    for metric in ("ibx_network_utilization_percent", "ibx_network_total_ips", "ibx_network_used_ips"):
        line = [l for l in output.split("\n") if l.startswith(metric)][0]
        assert 'shared="true"' in line, f"missing shared label in: {line}"


def test_network_metrics_no_shared_label_by_default():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_network_records(), None)
    assert "shared" not in output


# ── Formatter: fixedaddress metrics ───────────────────────────────

def test_fixedaddress_includes_shared_label():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_fixedaddr_records(), None, shared=True)
    line = [l for l in output.split("\n") if l.startswith("ibx_fixedaddress")][0]
    assert 'shared="true"' in line


def test_fixedaddress_no_shared_label_by_default():
    fmt = get_formatter("prometheus")
    output = fmt.render(_sample_fixedaddr_records(), None)
    assert "shared" not in output


# ── DNS zone-records renderer ─────────────────────────────────────

def test_dns_prometheus_includes_shared_label():
    output = render_dns_prometheus(_sample_dns_counts(), shared=True)
    line = [l for l in output.split("\n") if l.startswith("ibx_dns_records_count")][0]
    assert 'shared="true"' in line


def test_dns_prometheus_no_shared_label_by_default():
    output = render_dns_prometheus(_sample_dns_counts())
    assert "shared" not in output


# ── CLI wiring ────────────────────────────────────────────────────

@pytest.fixture
def patched_client(monkeypatch):
    """Patch _ensure_client so commands get a fake executor without network."""
    import ibxcli.cli.main as cli_main

    def fake_ensure_client(ctx):
        executor = MagicMock()
        ctx.obj["client"] = MagicMock()
        ctx.obj["executor"] = executor

    monkeypatch.setattr(cli_main, "_ensure_client", fake_ensure_client)


def _invoke_with_records(args, records):
    """Run a CLI command with the executor pre-configured to return records."""
    import ibxcli.cli.main as cli_main
    from ibxcli.cli.main import cli

    real_ensure = cli_main._ensure_client

    def ensure_with_result(ctx):
        real_ensure(ctx)
        ctx.obj["executor"].execute.return_value = QueryResult(
            records=records, fields=[], total_count=len(records))

    runner = CliRunner()
    # Patch again on top of the fixture's patch to wire execute results
    import unittest.mock as um
    with um.patch.object(cli_main, "_ensure_client", ensure_with_result):
        return runner.invoke(cli, args)


def test_utilization_cli_shared_flag(patched_client):
    result = _invoke_with_records(
        ["dhcp", "utilization", "--shared"], _sample_network_records())
    assert result.exit_code == 0, result.output
    assert 'shared="true"' in result.output


def test_utilization_cli_without_shared_flag(patched_client):
    result = _invoke_with_records(
        ["dhcp", "utilization"], _sample_network_records())
    assert result.exit_code == 0, result.output
    assert "shared" not in result.output


def test_fixed_addresses_cli_shared_flag(patched_client):
    result = _invoke_with_records(
        ["dhcp", "fixed-addresses", "--format", "prometheus", "--shared"],
        _sample_fixedaddr_records())
    assert result.exit_code == 0, result.output
    assert 'shared="true"' in result.output


def test_zone_records_cli_shared_flag(patched_client):
    records = [
        {"name": "www.example.com", "type": "A", "address": "10.0.0.1",
         "view": "default", "zone": "example.com", "ttl": 300},
        {"name": "mail.example.com", "type": "A", "address": "10.0.0.2",
         "view": "default", "zone": "example.com", "ttl": 300},
    ]
    result = _invoke_with_records(
        ["dns", "zone-records", "--zone", "example.com", "--shared"], records)
    assert result.exit_code == 0, result.output
    assert 'shared="true"' in result.output
