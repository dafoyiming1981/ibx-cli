"""JSON formatter."""

import json
from ibxcli.formatters.base import BaseFormatter, register_formatter


@register_formatter("json")
class JsonFormatter(BaseFormatter):
    def render(self, records: list[dict], fields: list[str] | None) -> str:
        if fields:
            records = [{k: v for k, v in r.items() if k in fields} for r in records]
        return json.dumps(records, indent=2, ensure_ascii=False)
