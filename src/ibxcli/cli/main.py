"""Root CLI group and global options for ibx-cli."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from ibxcli import __version__
from ibxcli.core.client import IbxClient
from ibxcli.core.config import DEFAULT_CONFIG_PATH, load_config
from ibxcli.core.exceptions import IbxAuthError, IbxConfigError, IbxConnectionError, IbxWapiError
from ibxcli.core.query import QueryExecutor
from ibxcli.formatters.base import get_formatter

console = Console(stderr=True)


def output_options(f):
    """Decorator adding --format, --fields, --limit, --sort to a command."""
    f = click.option("--format", "output_format", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")(f)
    f = click.option("--fields", help="Comma-separated fields to display")(f)
    f = click.option("--limit", type=int, default=100, show_default=True, help="Max rows to display")(f)
    f = click.option("--sort", help="Sort results by field")(f)
    return f


def execute_and_render(ctx, obj_type, search_filters, **kwargs):
    """Common pattern: build query, execute, render results."""
    _ensure_client(ctx)
    from ibxcli.objects import HANDLERS

    handler = HANDLERS.get(obj_type)
    if handler is None:
        console.print(f"[red]Unknown object type: {obj_type}[/red]")
        sys.exit(1)

    params = ctx.obj["executor"].build_params(
        obj_type=obj_type,
        search_filters=search_filters,
        default_fields=handler.default_return_fields,
    )

    fmt = ctx.params.get("output_format", "table")
    fields_override = ctx.params.get("fields")
    limit = ctx.params.get("limit", 100)
    sort_by = ctx.params.get("sort")

    if fields_override:
        params.return_fields = [f.strip() for f in fields_override.split(",")]
    params.limit = limit
    params.sort_by = sort_by

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

    formatter = get_formatter(fmt)
    console.print(formatter.render(result.records, result.fields), soft_wrap=True)


def _resolve_config(ctx: click.Context):
    """Merge config file, env vars, and CLI flags into ConnectionConfig."""
    cli_overrides = {}
    for key in ("host", "username", "password", "wapi_version", "ssl_verify", "timeout", "max_results"):
        val = ctx.params.get(key)
        if val is not None:
            cli_overrides[key] = val

    config_path = ctx.params.get("config")
    profile = ctx.params.get("profile")
    cfg_file = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    return load_config(config_path=cfg_file, profile=profile, cli_overrides=cli_overrides)


def _ensure_client(ctx):
    """Lazy config resolution — only when a leaf command needs the client."""
    if "client" not in ctx.obj:
        cfg = _resolve_config(ctx)
        try:
            client = IbxClient(cfg)
        except (IbxConnectionError, IbxAuthError, IbxError) as e:
            console.print(f"[red]Connection error:[/red] {e}")
            sys.exit(1)
        ctx.obj["client"] = client
        ctx.obj["executor"] = QueryExecutor(client)
        ctx.obj["config"] = cfg


@click.group(invoke_without_command=True)
@click.option("--config", type=click.Path(), help="Config file path (default: ~/.infoblox/config)")
@click.option("--profile", help="Use named profile from config file")
@click.option("--host", help="Infoblox Grid Master hostname or IP")
@click.option("--username", help="API username")
@click.option("--password", help="API password (or set IBX_PASSWORD env)")
@click.option("--wapi-version", default=None, help="WAPI version (default: 2.13)")
@click.option("--no-verify-ssl", is_flag=True, help="Disable SSL certificate verification")
@click.option("--timeout", type=int, default=None, help="Request timeout in seconds (default: 30)")
@click.option("--max-results", type=int, default=None, help="Max results per query (default: 1000)")
@click.version_option(__version__, prog_name="ibx")
@click.pass_context
def cli(ctx, config, profile, host, username, password, wapi_version, no_verify_ssl, timeout, max_results):
    """ibx - Infoblox NIOS CLI tool for DNS/DHCP management.

    Query and inspect DNS records, DHCP networks, leases, and more
    via the Infoblox WAPI.
    """
    ctx.ensure_object(dict)


# Register subcommand groups (import after cli is defined to avoid circular imports)
from ibxcli.cli.config import config  # noqa: E402
from ibxcli.cli.dns import dns  # noqa: E402
from ibxcli.cli.dhcp import dhcp  # noqa: E402
from ibxcli.cli.infra import infra  # noqa: E402
from ibxcli.cli.search import search_cmd  # noqa: E402

cli.add_command(config)
cli.add_command(dns)
cli.add_command(dhcp)
cli.add_command(infra)
cli.add_command(search_cmd)
