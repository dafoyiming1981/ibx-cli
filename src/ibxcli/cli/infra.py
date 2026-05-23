"""Infrastructure command group."""

import click

from ibxcli.cli.main import execute_and_render, output_options
from ibxcli.objects import HANDLERS


@click.group()
def infra():
    """Infrastructure management commands."""
    pass


@infra.command()
@output_options
@click.pass_context
def grid(ctx, **kwargs):
    """Show grid properties."""
    handler = HANDLERS["grid"]
    filters = handler.build_search_filters()
    execute_and_render(ctx, "grid", filters, **kwargs)


@infra.command()
@output_options
@click.option("--host-name", help="Member hostname filter")
@click.option("--service-state", help="Service state filter")
@click.pass_context
def members(ctx, host_name, service_state, **kwargs):
    """List grid members."""
    handler = HANDLERS["member"]
    filters = handler.build_search_filters(host_name=host_name, service_state=service_state)
    execute_and_render(ctx, "member", filters, **kwargs)


@infra.command()
@output_options
@click.option("--name", help="DNS view name filter")
@click.option("--network-view", help="Associated network view filter")
@click.pass_context
def views(ctx, name, network_view, **kwargs):
    """List DNS views."""
    handler = HANDLERS["view"]
    filters = handler.build_search_filters(name=name, network_view=network_view)
    execute_and_render(ctx, "view", filters, **kwargs)


@infra.command()
@output_options
@click.option("--name", help="Network view name filter")
@click.pass_context
def network_views(ctx, name, **kwargs):
    """List network views."""
    handler = HANDLERS["networkview"]
    filters = handler.build_search_filters(name=name)
    execute_and_render(ctx, "networkview", filters, **kwargs)
