"""Global cross-object search command."""

import click
from rich.console import Console

from ibxcli.core.exceptions import IbxConnectionError, IbxAuthError, IbxWapiError

console = Console(stderr=True)


@click.command("search")
@click.argument("query")
@click.option("--type", "obj_type", help="Limit search to object type (e.g., record:a, network)")
@click.option("--by", type=click.Choice(["address", "fqdn", "mac_address"]), default="address",
              help="Search field type (default: address)")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
@click.option("--fields", help="Comma-separated fields to display")
@click.option("--limit", type=int, default=100, show_default=True, help="Max rows to display")
@click.option("--sort", help="Sort results by field")
@click.pass_context
def search_cmd(ctx, query, obj_type, by, output_format, fields, limit, sort):
    """Search across all objects.

    QUERY is the search string. Use --by to specify what field to search
    (address, fqdn, mac_address). Use --type to limit the object types searched.
    """
    client = ctx.obj.get("client")
    if client is None:
        console.print("[red]No client available[/red]")
        return

    field_map = {
        "address": "address",
        "fqdn": "fqdn",
        "mac_address": "mac_address",
    }
    search_field = field_map[by]

    if obj_type:
        obj_types = [obj_type]
    else:
        obj_types = ["record:a", "record:aaaa", "record:cname", "record:host", "record:ptr", "record:txt"]

    all_records = []
    for ot in obj_types:
        try:
            results = client.get(ot, {search_field: query})
            for r in results:
                r["_obj_type"] = ot
            all_records.extend(results)
        except (IbxConnectionError, IbxAuthError, IbxWapiError) as e:
            console.print(f"[yellow]Warning: search {ot} failed: {e}[/yellow]")

    if not all_records:
        console.print("[yellow]No results found.[/yellow]")
        return

    if limit:
        all_records = all_records[:limit]

    if fields:
        display_fields = [f.strip() for f in fields.split(",")]
    else:
        display_fields = ["_obj_type", "name", "address", "ipv4addr", "ipv6addr", "view", "zone"]
        display_fields = [f for f in display_fields if any(f in r for r in all_records)]

    from ibxcli.formatters.base import get_formatter
    formatter = get_formatter(output_format)
    console.print(formatter.render(all_records, display_fields), soft_wrap=True)
