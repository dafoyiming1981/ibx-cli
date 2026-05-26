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
    """Render networks with their DHCP ranges nested underneath."""
    from ibxcli.cli.main import _ensure_client, output_options as _output_options
    from ibxcli.formatters.base import get_formatter
    from rich.console import Console
    from rich.table import Table
    import io
    import sys

    _ensure_client(ctx)

    net_handler = HANDLERS["network"]
    range_handler = HANDLERS["range"]

    # Fetch networks
    net_params = ctx.obj["executor"].build_params(
        obj_type=net_handler.obj_type,
        search_filters=filters,
        default_fields=net_handler.default_return_fields,
    )
    fields_override = ctx.params.get("fields")
    if fields_override:
        net_params.return_fields = [f.strip() for f in fields_override.split(",")]
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
    Console(stderr=True).print(f"[cyan]DEBUG range_filters={range_filters}[/cyan]")
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

    Console(stderr=True).print(f"[cyan]DEBUG range_result count={len(range_result.records)}, fields={range_result.fields}[/cyan]")

    # DEBUG: dump first range to see actual fields
    if range_result.records:
        Console(stderr=True).print(f"[cyan]DEBUG range keys: {list(range_result.records[0].keys())}[/cyan]")
        Console(stderr=True).print(f"[cyan]DEBUG range[0]: {range_result.records[0]}[/cyan]")

    # Index ranges by network CIDR
    ranges_by_network = {}
    for r in range_result.records:
        net_cidr = r.get("network", "")
        if net_cidr:
            ranges_by_network.setdefault(net_cidr, []).append(r)

    Console(stderr=True).print(f"[cyan]DEBUG ranges_by_network keys: {list(ranges_by_network.keys())}[/cyan]")
    Console(stderr=True).print(f"[cyan]DEBUG networks: {[r.get('network','') for r in net_result.records]}[/cyan]")

    # Render
    net_fields = net_result.fields
    table = Table(show_header=True, header_style="bold cyan")

    # All columns are no_wrap for compactness
    for col in net_fields:
        table.add_column(col, no_wrap=True, max_width=60)

    for record in net_result.records:
        # Network row
        table.add_row(*[str(record.get(c, "")) for c in net_fields])

        # Range rows nested below
        cidr = record.get("network", "")
        child_ranges = ranges_by_network.get(cidr, [])
        for i, rng in enumerate(child_ranges):
            is_last = i == len(child_ranges) - 1
            prefix = "└─ " if is_last else "├─ "
            row_vals = []
            for j, col in enumerate(net_fields):
                if j == 0:
                    row_vals.append(prefix + str(rng.get("start_addr", "")))
                elif col == "members":
                    # Show Member Assignment: None, member hostname, or failover association
                    assoc_type = rng.get("server_association_type", "NONE")
                    if assoc_type == "MEMBER":
                        member_val = rng.get("member", "")
                        row_vals.append(member_val if member_val else "None")
                    elif assoc_type == "FAILOVER":
                        row_vals.append(str(rng.get("failover_association", "")))
                    else:
                        row_vals.append("None")
                elif col == "comment":
                    row_vals.append(str(rng.get("comment", "")))
                else:
                    row_vals.append("")
            table.add_row(*row_vals)

    out = io.StringIO()
    c = Console(file=out, width=160, force_terminal=False)
    c.print(table)
    Console().print(out.getvalue(), soft_wrap=True)


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
@click.option("--address", help="Leased IP address filter")
@click.option("--mac", help="Client MAC address filter")
@click.option("--network", help="Network filter")
@click.option("--state", type=click.Choice(["active", "expired"]), help="Lease state filter")
@click.pass_context
def leases(ctx, address, mac, network, state, **kwargs):
    """List DHCP leases."""
    handler = HANDLERS["lease"]
    filters = handler.build_search_filters(address=address, mac=mac, network=network, state=state)
    execute_and_render(ctx, "lease", filters, **kwargs)


@dhcp.command()
@output_options
@click.option("--network", help="Network filter")
@click.option("--status", type=click.Choice(["used", "free"]), help="Address status filter")
@click.option("--mac", help="MAC address filter")
@click.option("--name", help="Associated name filter")
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
