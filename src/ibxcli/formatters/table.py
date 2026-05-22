"""Rich table formatter."""

import io
from rich.console import Console
from rich.table import Table

from ibxcli.formatters.base import BaseFormatter, register_formatter


@register_formatter("table")
class TableFormatter(BaseFormatter):
    def render(self, records: list[dict], fields: list[str] | None) -> str:
        if not records:
            return ""

        cols = fields or list(records[0].keys())
        table = Table(show_header=True, header_style="bold cyan")
        for col in cols:
            table.add_column(col, no_wrap=True, max_width=40)

        for record in records:
            table.add_row(*[str(record.get(c, "")) for c in cols])

        f = io.StringIO()
        c = Console(file=f, force_terminal=True, width=160)
        c.print(table)
        return f.getvalue()
