"""CSV formatter."""

from __future__ import annotations

import csv
import io
from ibxcli.formatters.base import BaseFormatter, register_formatter


@register_formatter("csv")
class CsvFormatter(BaseFormatter):
    def render(self, records: list[dict], fields: list[str] | None) -> str:
        if not records:
            return ""

        cols = fields or list(records[0].keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue()
