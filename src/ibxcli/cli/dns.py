"""DNS command group."""

import click

from ibxcli.cli.main import execute_and_render, output_options
from ibxcli.objects import HANDLERS


@click.group()
def dns():
    """DNS management commands."""
    pass


@dns.command()
@output_options
@click.option("--view", help="DNS view filter")
@click.option("--fqdn", help="Zone FQDN filter (use --regex for pattern match)")
@click.option("--regex", is_flag=True, help="Treat fqdn as regex pattern")
@click.pass_context
def zones(ctx, view, fqdn, regex):
    """List authoritative DNS zones."""
    handler = HANDLERS["zone:auth"]
    filters = handler.build_search_filters(view=view, fqdn=fqdn, regex=regex)
    execute_and_render(ctx, "zone:auth", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter (use --regex for pattern match)")
@click.option("--ipv4addr", help="IPv4 address filter")
@click.option("--zone", help="Zone filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def a(ctx, name, ipv4addr, zone, view, regex):
    """List DNS A records."""
    handler = HANDLERS["record:a"]
    filters = handler.build_search_filters(name=name, ipv4addr=ipv4addr, zone=zone, view=view, regex=regex)
    execute_and_render(ctx, "record:a", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter (use --regex for pattern match)")
@click.option("--ipv6addr", help="IPv6 address filter")
@click.option("--zone", help="Zone filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def aaaa(ctx, name, ipv6addr, zone, view, regex):
    """List DNS AAAA records."""
    handler = HANDLERS["record:aaaa"]
    filters = handler.build_search_filters(name=name, ipv6addr=ipv6addr, zone=zone, view=view, regex=regex)
    execute_and_render(ctx, "record:aaaa", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter")
@click.option("--canonical", help="Canonical name filter")
@click.option("--zone", help="Zone filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def cname(ctx, name, canonical, zone, view, regex):
    """List DNS CNAME records."""
    handler = HANDLERS["record:cname"]
    filters = handler.build_search_filters(name=name, canonical=canonical, zone=zone, view=view, regex=regex)
    execute_and_render(ctx, "record:cname", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter")
@click.option("--zone", help="Zone filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def mx(ctx, name, zone, view, regex):
    """List DNS MX records."""
    handler = HANDLERS["record:mx"]
    filters = handler.build_search_filters(name=name, zone=zone, view=view, regex=regex)
    execute_and_render(ctx, "record:mx", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter")
@click.option("--zone", help="Zone filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def ns(ctx, name, zone, view, regex):
    """List DNS NS records."""
    handler = HANDLERS["record:ns"]
    filters = handler.build_search_filters(name=name, zone=zone, view=view, regex=regex)
    execute_and_render(ctx, "record:ns", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter")
@click.option("--zone", help="Zone filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def txt(ctx, name, zone, view, regex):
    """List DNS TXT records."""
    handler = HANDLERS["record:txt"]
    filters = handler.build_search_filters(name=name, zone=zone, view=view, regex=regex)
    execute_and_render(ctx, "record:txt", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter")
@click.option("--ipv4addr", help="IPv4 address filter")
@click.option("--ipv6addr", help="IPv6 address filter")
@click.option("--zone", help="Zone filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def ptr(ctx, name, ipv4addr, ipv6addr, zone, view, regex):
    """List DNS PTR records."""
    handler = HANDLERS["record:ptr"]
    filters = handler.build_search_filters(name=name, ipv4addr=ipv4addr, ipv6addr=ipv6addr, zone=zone, view=view, regex=regex)
    execute_and_render(ctx, "record:ptr", filters)


@dns.command()
@output_options
@click.option("--name", help="Record name filter")
@click.option("--ipv4addr", help="IPv4 address filter")
@click.option("--mac", help="MAC address filter")
@click.option("--view", help="DNS view filter")
@click.option("--regex", is_flag=True, help="Treat name as regex pattern")
@click.pass_context
def hosts(ctx, name, ipv4addr, mac, view, regex):
    """List DNS host records."""
    handler = HANDLERS["record:host"]
    filters = handler.build_search_filters(name=name, ipv4addr=ipv4addr, mac=mac, view=view, regex=regex)
    execute_and_render(ctx, "record:host", filters)


@dns.command("all-records")
@output_options
@click.option("--zone", required=True, help="Zone (required)")
@click.option("--view", help="DNS view filter")
@click.option("--type", "record_type", help="Filter by record type (A, CNAME, etc.)")
@click.pass_context
def all_records(ctx, zone, view, record_type):
    """List all DNS records in a zone."""
    handler = HANDLERS["allrecords"]
    filters = handler.build_search_filters(zone=zone, view=view, type=record_type)
    execute_and_render(ctx, "allrecords", filters)
