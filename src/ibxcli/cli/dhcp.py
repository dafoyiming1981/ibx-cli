"""DHCP command group."""

import click

from ibxcli.cli.main import execute_and_render, output_options
from ibxcli.objects import HANDLERS


@click.group()
def dhcp():
    """DHCP management commands."""
    pass


@dhcp.command()
@output_options
@click.option("--network", help="CIDR network filter (e.g., 10.0.0.0/24)")
@click.option("--network-view", help="Network view filter")
@click.option("--with-ranges", is_flag=True, help="Show DHCP ranges under each network")
@click.pass_context
def networks(ctx, network, network_view, with_ranges, **kwargs):
    """List IPv4 networks."""
    handler = HANDLERS["network"]
    filters = handler.build_search_filters(network=network, network_view=network_view)
    if with_ranges:
        _render_networks_with_ranges(ctx, handler, filters, **kwargs)
    else:
        execute_and_render(ctx, "network", filters, **kwargs)


def _render_networks_with_ranges(ctx, handler, filters, **kwargs):
    """Render networks with their DHCP ranges nested underneath, with failover tree view."""
    from ibxcli.cli.main import _ensure_client
    from rich.console import Console

    _ensure_client(ctx)

    net_handler = HANDLERS["network"]
    range_handler = HANDLERS["range"]

    # Fetch networks with extattrs
    net_params = ctx.obj["executor"].build_params(
        obj_type=net_handler.obj_type,
        search_filters=filters,
        default_fields=net_handler.default_return_fields,
    )
    net_params.return_fields.append("extattrs")
    net_params.limit = ctx.params.get("limit", 100)
    net_params.sort_by = ctx.params.get("sort")

    try:
        net_result = ctx.obj["executor"].execute(net_params)
    except Exception as e:
        Console(stderr=True).print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if not net_result.records:
        Console(stderr=True).print("[yellow]No networks found.[/yellow]")
        return

    # Fetch ranges grouped by network CIDR
    range_filters = range_handler.build_search_filters(network_view=ctx.params.get("network_view"))
    range_params = ctx.obj["executor"].build_params(
        obj_type=range_handler.obj_type,
        search_filters=range_filters,
        default_fields=range_handler.default_return_fields,
    )
    range_params.limit = None  # no limit for ranges
    try:
        range_result = ctx.obj["executor"].execute(range_params)
    except Exception as e:
        Console(stderr=True).print(f"[red]Error fetching ranges:[/red] {e}")
        sys.exit(1)

    # Index ranges by network CIDR
    ranges_by_network = {}
    for r in range_result.records:
        net_cidr = r.get("network", "")
        if net_cidr:
            ranges_by_network.setdefault(net_cidr, []).append(r)

    # Render
    out = Console(width=160, force_terminal=False)
    for i, record in enumerate(net_result.records):
        if i > 0:
            out.print()  # blank line between members

        cidr = record.get("network", "")
        net_ea = record.get("extattrs", {})
        net_vlan = net_ea.get("VLAN", {}).get("value", "")
        net_zone = net_ea.get("Zone", {}).get("value", "")
        net_site = net_ea.get("Site", {}).get("value", "")
        net_comment = record.get("comment", "")

        # Build network header
        header = f"[bold]{cidr}[/bold]"
        header_parts = []
        if net_comment:
            header_parts.append(f"[dim]{net_comment}[/dim]")
        ea_parts = []
        if net_vlan:
            ea_parts.append(f"VLAN: {net_vlan}")
        if net_zone:
            ea_parts.append(f"Zone: {net_zone}")
        if net_site:
            ea_parts.append(f"Site: {net_site}")
        if ea_parts:
            header_parts.append(f"[dim]{' | '.join(ea_parts)}[/dim]")
        if header_parts:
            header += f"  {'  '.join(header_parts)}"
        out.print(header)

        child_ranges = ranges_by_network.get(cidr, [])
        if not child_ranges:
            out.print("  [dim]└── No DHCP ranges configured[/dim]")
            continue

        for idx, rng in enumerate(child_ranges):
            is_last = idx == len(child_ranges) - 1
            connector = "└─" if is_last else "├─"

            start = rng.get("start_addr", "")
            end = rng.get("end_addr", "")
            assoc_type = rng.get("server_association_type", "NONE")

            # Build assignment description with color coding
            if assoc_type == "MEMBER":
                member_val = rng.get("member", "")
                assignment = f"[green]{member_val}[/green]" if member_val else "[dim]None[/dim]"
                tag = "[dim]MEMBER[/dim]"
            elif assoc_type == "FAILOVER":
                fo_name = rng.get("failover_association", "")
                assignment = f"[yellow]{fo_name}[/yellow]" if fo_name else "[dim]None[/dim]"
                tag = "[bold yellow]FAILOVER[/bold yellow]"
            elif assoc_type == "MS_SERVER":
                assignment = "[cyan]MS DHCP[/cyan]"
                tag = "[dim]MS_SERVER[/dim]"
            else:
                assignment = "[dim]None[/dim]"
                tag = "[dim]NONE[/dim]"

            # DDNS info
            ddns_updates = rng.get("enable_ddns")
            ddns_domain = rng.get("ddns_domainname", "")
            ddns_parts = []
            if ddns_updates is True:
                ddns_parts.append("DDNS: [green]ON[/green]")
                if ddns_domain:
                    ddns_parts[-1] += f" [dim]({ddns_domain})[/dim]"
            elif ddns_updates is False:
                ddns_parts.append("DDNS: [dim]OFF[/dim]")

            # VLAN / Zone / Site (from range itself, falling back to network)
            rng_vlan = rng.get("VLAN", "") or net_vlan
            rng_zone = rng.get("Zone", "") or net_zone
            rng_site = rng.get("Site", "") or net_site
            ea_parts = []
            if rng_vlan:
                ea_parts.append(f"VLAN: {rng_vlan}")
            if rng_zone:
                ea_parts.append(f"Zone: {rng_zone}")
            if rng_site:
                ea_parts.append(f"Site: {rng_site}")

            # Build full line
            line = f"  {connector} [cyan]{start} - {end}[/cyan]  {tag}  → {assignment}"
            if ddns_parts:
                line += f"  {'  '.join(ddns_parts)}"
            if ea_parts:
                line += f"  [dim]{' | '.join(ea_parts)}[/dim]"
            out.print(line)


@dhcp.command()
@output_options
@click.option("--network", help="CIDR IPv6 network filter")
@click.option("--network-view", help="Network view filter")
@click.pass_context
def ipv6_networks(ctx, network, network_view, **kwargs):
    """List IPv6 networks."""
    handler = HANDLERS["ipv6network"]
    filters = handler.build_search_filters(network=network, network_view=network_view)
    execute_and_render(ctx, "ipv6network", filters, **kwargs)


@dhcp.command()
@output_options
@click.option("--network", help="CIDR container network filter")
@click.option("--network-view", help="Network view filter")
@click.pass_context
def containers(ctx, network, network_view, **kwargs):
    """List network containers."""
    handler = HANDLERS["networkcontainer"]
    filters = handler.build_search_filters(network=network, network_view=network_view)
    execute_and_render(ctx, "networkcontainer", filters, **kwargs)


@dhcp.command()
@output_options
@click.option("--ipv4addr", help="IPv4 address filter")
@click.option("--mac", help="MAC address filter")
@click.option("--network-view", help="Network view filter")
@click.pass_context
def fixed_addresses(ctx, ipv4addr, mac, network_view, **kwargs):
    """List DHCP fixed addresses (reservations)."""
    handler = HANDLERS["fixedaddress"]
    filters = handler.build_search_filters(ipv4addr=ipv4addr, mac=mac, network_view=network_view)
    execute_and_render(ctx, "fixedaddress", filters, **kwargs)


@dhcp.command()
@output_options
@click.option("--network", help="CIDR network filter (e.g., 10.0.0.0/24)")
@click.option("--status", help="Lease status filter")
@click.option("--mac", help="MAC address filter")
@click.option("--name", help="Client name filter")
@click.pass_context
def ipv4_addresses(ctx, network, status, mac, name, **kwargs):
    """List IPv4 address usage status."""
    handler = HANDLERS["ipv4address"]
    filters = handler.build_search_filters(network=network, status=status, mac=mac, name=name)
    execute_and_render(ctx, "ipv4address", filters, **kwargs)


@dhcp.command()
@output_options
@click.option("--network", help="CIDR network filter (e.g., 10.0.0.0/24)")
@click.option("--network-view", help="Network view filter")
@click.pass_context
def ranges(ctx, network, network_view, **kwargs):
    """List DHCP address ranges."""
    handler = HANDLERS["range"]
    filters = handler.build_search_filters(network=network, network_view=network_view)
    execute_and_render(ctx, "range", filters, **kwargs)


@dhcp.command()
@output_options
@click.option("--network", help="CIDR network filter (e.g., 10.0.0.0/24)")
@click.option("--network-view", help="Network view filter")
@click.pass_context
def leases(ctx, network, network_view, **kwargs):
    """List DHCP leases."""
    handler = HANDLERS["lease"]
    filters = handler.build_search_filters(network=network, network_view=network_view)
    execute_and_render(ctx, "lease", filters, **kwargs)
