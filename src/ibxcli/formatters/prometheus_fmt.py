"""Prometheus text format exporter."""

from __future__ import annotations

from ibxcli.formatters.base import BaseFormatter, register_formatter


def _sanitize_label(value: str) -> str:
    """Escape double quotes and backslashes for Prometheus label values."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _label_set(network: str, vlan: str = "", zone: str = "", site: str = "", members: str = "") -> str:
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
    return "{" + ",".join(parts) + "}"


@register_formatter("prometheus")
class PrometheusFormatter(BaseFormatter):
    """Render network utilization records as Prometheus text exposition format."""

    def render(self, records: list[dict], fields: list[str] | None) -> str:
        lines: list[str] = []

        for rec in records:
            network = rec.get("network", "")
            utilization = rec.get("utilization", 0)
            vlan = rec.get("VLAN", "")
            zone = rec.get("Zone", "")
            site = rec.get("Site", "")
            members = rec.get("members", "")

            lbl = _label_set(network, vlan, zone, site, members)

            # WAPI returns utilization as per-mille (0-1000), convert to percent (0-100)
            utilization_pct = round(utilization / 10, 1)

            lines.append("# HELP ibx_network_utilization_percent Network utilization percentage (0-100)")
            lines.append("# TYPE ibx_network_utilization_percent gauge")
            lines.append(f"ibx_network_utilization_percent{lbl} {utilization_pct}")
            lines.append("")

            cidr_parts = network.split("/")
            if len(cidr_parts) == 2:
                try:
                    prefix = int(cidr_parts[1])
                    total_ips = 2 ** (32 - prefix) - 2
                    if total_ips > 0:
                        used_ips = round(total_ips * utilization_pct / 100)
                        lines.append("# HELP ibx_network_total_ips Total IPs in the network")
                        lines.append("# TYPE ibx_network_total_ips gauge")
                        lines.append(f"ibx_network_total_ips{lbl} {total_ips}")
                        lines.append("")
                        lines.append("# HELP ibx_network_used_ips Used IPs in the network")
                        lines.append("# TYPE ibx_network_used_ips gauge")
                        lines.append(f"ibx_network_used_ips{lbl} {used_ips}")
                        lines.append("")
                except ValueError:
                    pass

        lines.append("")
        return "\n".join(lines)
