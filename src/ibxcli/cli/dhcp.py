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
@click.pass_context
def networks(ctx, network, network_view, **kwargs):
    """List IPv4 networks."""
    handler = HANDLERS["network"]
    filters = handler.build_search_filters(network=network, network_view=network_view)
    execute_and_render(ctx, "network", filters, **kwargs)


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
