"""Root CLI group and global options for ibx-cli."""

from __future__ import annotations

import getpass
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
    f = click.option("--format", "output_format", type=click.Choice(["table", "json", "csv", "prometheus"]), default="table", help="Output format")(f)
    f = click.option("--fields", help="Comma-separated fields to display")(f)
    f = click.option("--limit", type=int, default=None, help="Max rows to display (default: all)")(f)
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
        obj_type=handler.obj_type,
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

    cfg = load_config(config_path=cfg_file, profile=profile, cli_overrides=cli_overrides)

    # If password is still empty and not using Vault, prompt interactively
    vault_mode = bool(cfg.vault_addr and cfg.vault_cert_path and cfg.vault_key_path and cfg.vault_secret_path)
    if not cfg.password and not ctx.params.get("password") and not vault_mode:
        cfg.password = getpass.getpass("Password: ")

    return cfg


def _print_debug_config(cfg):
    """Print resolved config for debugging (password masked)."""
    vault_mode = bool(cfg.vault_addr and cfg.vault_cert_path and cfg.vault_key_path and cfg.vault_secret_path)

    console.print("\n=== ibx-cli Debug Info ===\n")

    console.print("[bold]Authentication Mode:[/bold]")
    if vault_mode:
        console.print("  [green]Vault TLS cert auth[/green]")
    elif cfg.password:
        console.print("  [green]Password configured[/green]")
    else:
        console.print("  [red]No password configured[/red]")

    console.print("\n[bold]Infoblox Connection:[/bold]")
    console.print(f"  host:         {cfg.host or '(not set)'}")
    console.print(f"  username:     {cfg.username or '(not set)'}")
    console.print(f"  password:     {'*' * len(cfg.password) if cfg.password else '(empty)'}")
    console.print(f"  wapi_version: {cfg.wapi_version}")
    console.print(f"  ssl_verify:   {cfg.ssl_verify}")

    console.print("\n[bold]Vault Configuration:[/bold]")
    console.print(f"  vault_addr:       {cfg.vault_addr or '(not set)'}")
    console.print(f"  vault_cert_path:  {cfg.vault_cert_path or '(not set)'}")
    console.print(f"  vault_key_path:   {cfg.vault_key_path or '(not set)'}")
    console.print(f"  vault_secret_path: {cfg.vault_secret_path or '(not set)'}")
    console.print(f"  vault_role_name:  {cfg.vault_role_name or '(not set)'}")
    console.print(f"  vault_mount_path: {cfg.vault_mount_path or '(not set)'}")

    # Highlight missing vault vars
    if not vault_mode:
        missing = []
        if not cfg.vault_addr:
            missing.append("IBX_VAULT_ADDR")
        if not cfg.vault_cert_path:
            missing.append("IBX_VAULT_CERT_PATH")
        if not cfg.vault_key_path:
            missing.append("IBX_VAULT_KEY_PATH")
        if not cfg.vault_secret_path:
            missing.append("IBX_VAULT_SECRET_PATH")
        if missing:
            console.print(f"\n  [yellow]Vault mode NOT active. Missing: {', '.join(missing)}[/yellow]")
        if cfg.host and cfg.username:
            console.print(f"\n  Falling back to [bold]username/password[/bold] auth.")

    console.print("")


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
@click.option("--password", help="API password (or set IBX_PASSWORD env, or enter interactively)")
@click.option("--wapi-version", default=None, help="WAPI version (default: 2.13)")
@click.option("--no-verify-ssl", is_flag=True, help="Disable SSL certificate verification")
@click.option("--timeout", type=int, default=None, help="Request timeout in seconds (default: 30)")
@click.option("--max-results", type=int, default=None, help="Max results per query (default: 1000)")
@click.option("--debug", is_flag=True, help="Print resolved config (password masked) and exit")
@click.version_option(__version__, prog_name="ibx")
@click.pass_context
def cli(ctx, config, profile, host, username, password, wapi_version, no_verify_ssl, timeout, max_results, debug):
    """ibx - Infoblox NIOS CLI tool for DNS/DHCP management.

    Query and inspect DNS records, DHCP networks, leases, and more
    via the Infoblox WAPI.
    """
    ctx.ensure_object(dict)

    if debug:
        cfg = _resolve_config(ctx)
        _print_debug_config(cfg)
        sys.exit(0)


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
