"""Tests for --fields behavior across all DNS record types.

Each test mocks the WAPI response and verifies that:
1. The handler's default_return_fields match what the mock returns
2. The QueryExecutor correctly extracts EONID from extattrs
3. The TableFormatter renders with the expected fields
4. The --fields override works correctly
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from ibxcli.objects.dns import (
    ARecordHandler, AAAARecordHandler, CNAMERecordHandler,
    MXRecordHandler, NSRecordHandler, TXTRecordHandler,
    PTRRecordHandler, HostRecordHandler, AuthZoneHandler,
    AllRecordsHandler,
)
from ibxcli.core.query import QueryExecutor
from ibxcli.formatters.table import TableFormatter
from ibxcli.formatters.json_fmt import JsonFormatter


# ── Fake WAPI responses ──────────────────────────────────────────

def _make_record(fields: dict, eonid: str = "TEST-001") -> dict:
    """Build a fake WAPI response record with extattrs and _ref."""
    record = dict(fields, _ref=f"fake/ref/{fields.get('name', 'unknown')}")
    record["extattrs"] = {"EONID": {"value": eonid}}
    return record


FAKE_A = [
    _make_record({"name": "www.example.com", "ipv4addr": "10.0.0.1", "view": "default",
                  "zone": "example.com", "ttl": 300, "comment": "web server"}),
    _make_record({"name": "api.example.com", "ipv4addr": "10.0.0.2", "view": "default",
                  "zone": "example.com", "ttl": 60, "comment": ""}),
]

FAKE_AAAA = [
    _make_record({"name": "ipv6.example.com", "ipv6addr": "2001:db8::1", "view": "default",
                  "zone": "example.com", "ttl": 300, "comment": "ipv6 host"}),
]

FAKE_CNAME = [
    _make_record({"name": "alias.example.com", "canonical": "www.example.com", "view": "default",
                  "zone": "example.com", "ttl": 3600, "comment": "alias"}),
]

FAKE_MX = [
    _make_record({"name": "example.com", "mail_exchanger": "mail.example.com", "preference": 10,
                  "view": "default", "zone": "example.com", "ttl": 3600}),
]

FAKE_NS = [
    _make_record({"name": "example.com", "nameserver": "ns1.example.com", "view": "default",
                  "zone": "example.com", "ttl": 86400}),
]

FAKE_TXT = [
    _make_record({"name": "_dmarc.example.com", "text": "v=DMARC1; p=reject", "view": "default",
                  "zone": "example.com", "ttl": 3600, "comment": "dmarc policy"}),
]

FAKE_PTR = [
    _make_record({"name": "1.0.0.10.in-addr.arpa", "ptrdname": "host.example.com",
                  "ipv4addr": "10.0.0.1", "ipv6addr": "", "view": "default",
                  "zone": "10.in-addr.arpa", "ttl": 300}),
]

FAKE_HOST = [
    _make_record({"name": "server1.example.com", "ipv4addrs": ["10.0.0.10"],
                  "view": "default", "comment": "physical server"}),
]

FAKE_ZONES = [
    _make_record({"fqdn": "example.com", "view": "default", "zone_format": "FORWARD",
                  "comment": "production zone"}),
]

FAKE_ALL_RECORDS = [
    _make_record({"name": "www.example.com", "type": "A", "address": "10.0.0.1",
                  "view": "default", "zone": "example.com", "ttl": 300}),
    _make_record({"name": "alias.example.com", "type": "CNAME", "address": "www.example.com",
                  "view": "default", "zone": "example.com", "ttl": 3600}),
]


@pytest.fixture
def mock_client():
    return MagicMock()


def run_query(mock_client, handler, filters, fields_override=None, limit=100, sort_by=None):
    """Run a full query pipeline and return the QueryResult."""
    executor = QueryExecutor(mock_client)
    params = executor.build_params(
        obj_type=handler.obj_type,
        search_filters=filters,
        default_fields=handler.default_return_fields,
    )
    if fields_override:
        params.return_fields = [f.strip() for f in fields_override.split(",")]
    params.limit = limit
    params.sort_by = sort_by

    result = executor.execute(params)
    return result


# ── Handler default fields ────────────────────────────────────────

@pytest.mark.parametrize("handler_cls,expected_fields", [
    (ARecordHandler, ["name", "ipv4addr", "view", "zone", "ttl", "comment", "EONID"]),
    (AAAARecordHandler, ["name", "ipv6addr", "view", "zone", "ttl", "comment", "EONID"]),
    (CNAMERecordHandler, ["name", "canonical", "view", "zone", "ttl", "comment", "EONID"]),
    (MXRecordHandler, ["name", "mail_exchanger", "preference", "view", "zone", "ttl", "EONID"]),
    (NSRecordHandler, ["name", "nameserver", "view", "zone", "ttl", "EONID"]),
    (TXTRecordHandler, ["name", "text", "view", "zone", "ttl", "comment", "EONID"]),
    (PTRRecordHandler, ["name", "ptrdname", "ipv4addr", "ipv6addr", "view", "zone", "ttl", "EONID"]),
    (HostRecordHandler, ["name", "ipv4addrs", "view", "comment", "EONID"]),
    (AuthZoneHandler, ["fqdn", "view", "zone_format", "comment", "EONID"]),
    (AllRecordsHandler, ["name", "type", "address", "view", "zone", "ttl", "EONID"]),
])
def test_default_return_fields(handler_cls, expected_fields):
    handler = handler_cls()
    assert handler.default_return_fields == expected_fields


# ── EONID extraction ──────────────────────────────────────────────

@pytest.mark.parametrize("records,handler_cls", [
    (FAKE_A, ARecordHandler),
    (FAKE_AAAA, AAAARecordHandler),
    (FAKE_CNAME, CNAMERecordHandler),
    (FAKE_MX, MXRecordHandler),
    (FAKE_NS, NSRecordHandler),
    (FAKE_TXT, TXTRecordHandler),
    (FAKE_PTR, PTRRecordHandler),
    (FAKE_HOST, HostRecordHandler),
    (FAKE_ZONES, AuthZoneHandler),
    (FAKE_ALL_RECORDS, AllRecordsHandler),
])
def test_eonid_extracted_from_extattrs(mock_client, records, handler_cls):
    mock_client.get.return_value = records
    handler = handler_cls()
    result = run_query(mock_client, handler, {})
    assert "EONID" in result.fields
    for rec in result.records:
        assert "EONID" in rec
        assert rec["EONID"] == "TEST-001"


def test_eonid_missing_from_extattrs(mock_client):
    """Records without EONID in extattrs should get empty string."""
    record = {"name": "test.example.com", "ipv4addr": "10.0.0.1", "extattrs": {}}
    mock_client.get.return_value = [record]
    handler = ARecordHandler()
    result = run_query(mock_client, handler, {})
    assert result.records[0]["EONID"] == ""


# ── _ref removal ──────────────────────────────────────────────────

def test_ref_removed_from_records(mock_client):
    mock_client.get.return_value = FAKE_A
    handler = ARecordHandler()
    result = run_query(mock_client, handler, {})
    for rec in result.records:
        assert "_ref" not in rec


# ── Table rendering ───────────────────────────────────────────────

def test_table_render_default_fields(mock_client):
    mock_client.get.return_value = FAKE_A
    handler = ARecordHandler()
    result = run_query(mock_client, handler, {})

    formatter = TableFormatter()
    output = formatter.render(result.records, result.fields)

    assert "name" in output
    assert "ipv4addr" in output
    assert "EONID" in output
    assert "www.example.com" in output
    assert "10.0.0.1" in output


def test_table_render_override_fields(mock_client):
    mock_client.get.return_value = FAKE_A
    handler = ARecordHandler()
    result = run_query(mock_client, handler, {}, fields_override="name,ipv4addr")

    formatter = TableFormatter()
    output = formatter.render(result.records, result.fields)

    assert "name" in output
    assert "ipv4addr" in output
    assert "comment" not in output
    assert "zone" not in output


# ── Per-record-type --fields examples ─────────────────────────────

@pytest.mark.parametrize("handler_cls,records,filters,fields_override,must_contain,must_not_contain", [
    (
        ARecordHandler, FAKE_A, {"zone": "example.com"},
        "name,ipv4addr",
        ["www.example.com", "10.0.0.1"],
        ["comment", "zone"],
    ),
    (
        AAAARecordHandler, FAKE_AAAA, {"zone": "example.com"},
        "name,ipv6addr",
        ["ipv6.example.com", "2001:db8::1"],
        ["comment"],
    ),
    (
        CNAMERecordHandler, FAKE_CNAME, {"zone": "example.com"},
        "name,canonical",
        ["alias.example.com", "www.example.com"],
        ["comment"],
    ),
    (
        MXRecordHandler, FAKE_MX, {"zone": "example.com"},
        "name,mail_exchanger,preference",
        ["example.com", "mail.example.com", "10"],
        [],
    ),
    (
        NSRecordHandler, FAKE_NS, {"zone": "example.com"},
        "name,nameserver",
        ["example.com", "ns1.example.com"],
        [],
    ),
    (
        TXTRecordHandler, FAKE_TXT, {"name": "_dmarc"},
        "name,text,comment",
        ["_dmarc.example.com", "v=DMARC1", "dmarc policy"],
        ["zone"],
    ),
    (
        PTRRecordHandler, FAKE_PTR, {"zone": "10.in-addr.arpa"},
        "name,ptrdname,ipv4addr",
        ["1.0.0.10.in-addr.arpa", "host.example.com", "10.0.0.1"],
        ["ipv6addr"],
    ),
    (
        HostRecordHandler, FAKE_HOST, {"name": "server1"},
        "name,ipv4addrs",
        ["server1.example.com", "10.0.0.10"],
        ["comment"],
    ),
    (
        AuthZoneHandler, FAKE_ZONES, {},
        "fqdn,view",
        ["example.com", "default"],
        ["zone_format", "comment"],
    ),
    (
        AllRecordsHandler, FAKE_ALL_RECORDS, {"zone": "example.com"},
        "name,type,address",
        ["www.example.com", "CNAME", "10.0.0.1"],
        [],
    ),
])
def test_fields_override_per_type(
    mock_client, handler_cls, records, filters,
    fields_override, must_contain, must_not_contain
):
    """Verify --fields override for each DNS record type."""
    mock_client.get.return_value = records
    handler = handler_cls()
    result = run_query(mock_client, handler, filters, fields_override=fields_override)

    formatter = TableFormatter()
    output = formatter.render(result.records, result.fields)

    for text in must_contain:
        assert text in output, f"Expected '{text}' in output for {handler_cls.__name__} with --fields '{fields_override}'"

    for text in must_not_contain:
        assert text not in output, f"Did not expect '{text}' in output for {handler_cls.__name__} with --fields '{fields_override}'"


# ── JSON output ───────────────────────────────────────────────────

def test_json_output_fields(mock_client):
    import json
    mock_client.get.return_value = FAKE_A
    handler = ARecordHandler()
    result = run_query(mock_client, handler, {}, fields_override="name,ipv4addr")

    formatter = JsonFormatter()
    output = formatter.render(result.records, result.fields)
    data = json.loads(output)

    assert len(data) == 2
    for rec in data:
        assert "name" in rec
        assert "ipv4addr" in rec


# ── Limit ─────────────────────────────────────────────────────────

def test_limit_truncates(mock_client):
    mock_client.get.return_value = FAKE_A
    handler = ARecordHandler()
    result = run_query(mock_client, handler, {}, limit=1)
    assert len(result.records) == 1
