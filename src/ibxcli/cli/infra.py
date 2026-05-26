"""Infrastructure command group."""

import sys

import click
from rich.console import Console

from ibxcli.cli.main import execute_and_render, output_options
from ibxcli.core.exceptions import IbxConnectionError, IbxAuthError, IbxWapiError
from ibxcli.objects import HANDLERS

console = Console(stderr=True)


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
@click.option("--host-name", help="Member hostname filter")
@click.option("--service-state", help="Service state filter")
@click.pass_context
def members(ctx, host_name, service_state, **kwargs):
    """List grid members with node-level HA status."""
    from ibxcli.cli.main import _ensure_client

    _ensure_client(ctx)

    handler = HANDLERS["member"]
    filters = handler.build_search_filters(host_name=host_name, service_state=service_state)

    params = ctx.obj["executor"].build_params(
        obj_type=handler.obj_type,
        search_filters=filters,
        default_fields=handler.default_return_fields,
    )

    try:
        result = ctx.obj["executor"].execute(params)
    except IbxConnectionError as e:
        console.print(f"[red]Connection error:[/red] {e}")
        sys.exit(1)
    except IbxAuthError as e:
        console.print(f"[red]Auth error:[/red] {e}")
        sys.exit(1)
    except IbxWapiError as e:
        console.print(f"[red]WAPI error:[/red] {e.wapi_text or e}")
        sys.exit(1)

    if not result.records:
        console.print("[yellow]No results found.[/yellow]")
        return

    # Render grouped table: member header + indented node rows
    out = Console(width=160, force_terminal=False)
    for i, record in enumerate(result.records):
        if i > 0:
            out.print()  # blank line between members

        host = record.get("host_name", "unknown")
        platform = record.get("platform", "")
        header = f"[bold]{host}[/bold]"
        if platform:
            header += f"  [dim]platform: {platform}[/dim]"
        out.print(header)

        node_info = record.get("node_info")
        if isinstance(node_info, list) and node_info:
            for idx, node in enumerate(node_info):
                ha = node.get("ha_status", "unknown")
                color = "green" if ha.lower() == "active" else ("yellow" if ha.lower() == "passive" else "red")
                out.print(f"  [dim]├──[/dim] [cyan]Node {idx + 1}[/cyan]  ha_status: [{color}]{ha}[/{color}]")
        else:
            out.print("  [dim]├──[/dim] [dim]No node info available[/dim]")


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
