"""Rich table formatter."""

from __future__ import annotations

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
            table.add_column(col, no_wrap=True, max_width=80)

        for record in records:
            row_data = []
            for c in cols:
                val = record.get(c, "")
                if isinstance(val, list):
                    val = str(val)
                row_data.append(str(val))
            table.add_row(*row_data)

        f = io.StringIO()
        c = Console(file=f, width=160, force_terminal=False)
        c.print(table)
        return f.getvalue()
