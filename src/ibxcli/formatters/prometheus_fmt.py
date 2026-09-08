"""Prometheus text format exporter."""

from __future__ import annotations

from ibxcli.formatters.base import BaseFormatter, register_formatter


def _sanitize_label(value: str) -> str:
    """Escape double quotes and backslashes for Prometheus label values."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_dns_prometheus(results: list[dict], shared: bool = False) -> str:
    """Render DNS record counts as Prometheus text exposition format."""
    lines = []
    for rec in results:
        label_set = f'zone="{rec["zone"]}"'
        if rec["view"]:
            label_set += f',view="{rec["view"]}"'
        label_set += f',type="{rec["type"]}"'
        if shared:
            label_set += ',shared="true"'
        lines.append(f'ibx_dns_records_count{{{label_set}}} {rec["count"]}')

    rendered_lines = [
        "# HELP ibx_dns_records_count Number of DNS records in the zone",
        "# TYPE ibx_dns_records_count gauge",
    ]
    rendered_lines.extend(lines)
    rendered_lines.append("")
    return "\n".join(rendered_lines)


def _label_set(network: str, vlan: str = "", zone: str = "", site: str = "", members: str = "", shared: bool = False) -> str:
    """Build Prometheus label set string."""
    net = f'network="{_sanitize_label(network)}"'
    parts = [net]
    if vlan:
        parts.append(f'vlan="{_sanitize_label(vlan)}"')
    if zone:
        parts.append(f'zone="{_sanitize_label(zone)}"')
    if site:
        parts.append(f'site="{_sanitize_label(site)}"')
    if members:
        parts.append(f'members="{_sanitize_label(members)}"')
    if shared:
        parts.append('shared="true"')
    return "{" + ",".join(parts) + "}"


@register_formatter("prometheus")
class PrometheusFormatter(BaseFormatter):
    """Render network utilization records as Prometheus text exposition format."""

    def render(self, records: list[dict], fields: list[str] | None, shared: bool = False) -> str:
        lines: list[str] = []
        seen_metrics: set[str] = set()

        for rec in records:
            # fixedaddress 记录：无 utilization 字段
            if "utilization" not in rec:
                self._render_fixedaddress(rec, lines, seen_metrics, shared=shared)
                continue

            network = rec.get("network", "")
            utilization = rec.get("utilization", 0)
            vlan = rec.get("VLAN", "")
            zone = rec.get("Zone", "")
            site = rec.get("Site", "")
            members = rec.get("members", "")

            lbl = _label_set(network, vlan, zone, site, members, shared=shared)
            utilization_pct = round(utilization / 10, 1)

            if "ibx_network_utilization_percent" not in seen_metrics:
                lines.append("# HELP ibx_network_utilization_percent Network utilization percentage (0-100)")
                lines.append("# TYPE ibx_network_utilization_percent gauge")
                seen_metrics.add("ibx_network_utilization_percent")
            lines.append(f"ibx_network_utilization_percent{lbl} {utilization_pct}")

            # Next 3 available IPs as info metric (IP values carried in labels).
            # Members label intentionally omitted to reduce series churn.
            next_ips = rec.get("next_available_ips")
            if isinstance(next_ips, list) and next_ips:
                if "ibx_network_next_available_ip" not in seen_metrics:
                    lines.append("# HELP ibx_network_next_available_ip Next 3 available IP addresses in the network")
                    lines.append("# TYPE ibx_network_next_available_ip gauge")
                    seen_metrics.add("ibx_network_next_available_ip")
                ip_labels = ",".join(
                    f'ip{i + 1}="{_sanitize_label(str(v))}"'
                    for i, v in enumerate(next_ips[:3])
                )
                base_lbl = _label_set(network, vlan, zone, site, shared=shared)
                lines.append(f"ibx_network_next_available_ip{base_lbl[:-1]},{ip_labels}}} 1")

            cidr_parts = network.split("/")
            if len(cidr_parts) == 2:
                try:
                    prefix = int(cidr_parts[1])
                    total_ips = 2 ** (32 - prefix) - 2
                    if total_ips > 0:
                        used_ips = round(total_ips * utilization_pct / 100)
                        if "ibx_network_total_ips" not in seen_metrics:
                            lines.append("# HELP ibx_network_total_ips Total IPs in the network")
                            lines.append("# TYPE ibx_network_total_ips gauge")
                            seen_metrics.add("ibx_network_total_ips")
                        lines.append(f"ibx_network_total_ips{lbl} {total_ips}")
                        if "ibx_network_used_ips" not in seen_metrics:
                            lines.append("# HELP ibx_network_used_ips Used IPs in the network")
                            lines.append("# TYPE ibx_network_used_ips gauge")
                            seen_metrics.add("ibx_network_used_ips")
                        lines.append(f"ibx_network_used_ips{lbl} {used_ips}")
                except ValueError:
                    pass

        lines.append("")
        return "\n".join(lines)

    def _render_fixedaddress(self, rec: dict, lines: list[str], seen_metrics: set[str], shared: bool = False) -> None:
        def _clean(v):
            return _sanitize_label((v or "").replace("\n", " "))

        if "ibx_fixedaddress" not in seen_metrics:
            lines.append("# HELP ibx_fixedaddress Fixed IP address reservations")
            lines.append("# TYPE ibx_fixedaddress gauge")
            seen_metrics.add("ibx_fixedaddress")

        lbl = (
            f'addr="{_clean(rec.get("ipv4addr"))}",'
            f'mac="{_clean(rec.get("mac"))}",'
            f'name="{_clean(rec.get("name"))}",'
            f'network="{_clean(rec.get("network"))}",'
            f'network_view="{_clean(rec.get("network_view"))}",'
            f'comment="{_clean(rec.get("comment"))}"'
        )
        if shared:
            lbl += ',shared="true"'
        lines.append(f"ibx_fixedaddress{{{lbl}}} 1")
