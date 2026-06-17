"""Prometheus text format exporter."""

from __future__ import annotations

from ibxcli.formatters.base import BaseFormatter, register_formatter


def _sanitize_label(value: str) -> str:
    """Escape double quotes and backslashes for Prometheus label values."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


@register_formatter("prometheus")
class PrometheusFormatter(BaseFormatter):
    """Render network utilization records as Prometheus text exposition format."""

    def render(self, records: list[dict], fields: list[str] | None) -> str:
        lines: list[str] = []

        lines.append("# HELP ibx_network_utilization_percent Network utilization percentage (0-100)")
        lines.append("# TYPE ibx_network_utilization_percent gauge")
        lines.append("# HELP ibx_network_total_ips Total IPs in the network")
        lines.append("# TYPE ibx_network_total_ips gauge")
        lines.append("# HELP ibx_network_used_ips Used IPs in the network")
        lines.append("# TYPE ibx_network_used_ips gauge")

        for rec in records:
            network = rec.get("network", "")
            utilization = rec.get("utilization", 0)
            vlan = rec.get("VLAN", "")
            zone = rec.get("Zone", "")
            site = rec.get("Site", "")
            members = rec.get("members", "")

            label_set = f'network="{_sanitize_label(network)}"'
            if vlan:
                label_set += f',vlan="{_sanitize_label(vlan)}"'
            if zone:
                label_set += f',zone="{_sanitize_label(zone)}"'
            if site:
                label_set += f',site="{_sanitize_label(site)}"'
            if members:
                label_set += f',members="{_sanitize_label(members)}"'

            lines.append(f"ibx_network_utilization_percent{{{label_set}}} {utilization}")

            cidr_parts = network.split("/")
            if len(cidr_parts) == 2:
                try:
                    prefix = int(cidr_parts[1])
                    total_ips = 2 ** (32 - prefix) - 2
                    if total_ips > 0:
                        used_ips = round(total_ips * utilization / 100)
                        lines.append(f"ibx_network_total_ips{{{label_set}}} {total_ips}")
                        lines.append(f"ibx_network_used_ips{{{label_set}}} {used_ips}")
                except ValueError:
                    pass

        lines.append("")
        return "\n".join(lines)
