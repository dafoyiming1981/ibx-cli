"""Query execution engine for ibx-cli."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QueryParams:
    """Parameters for a single WAPI query."""

    obj_type: str
    search_filters: dict = field(default_factory=dict)
    return_fields: list[str] = field(default_factory=list)
    limit: int = 100
    sort_by: str | None = None


@dataclass
class QueryResult:
    """Result of a WAPI query."""

    records: list[dict]
    fields: list[str]
    total_count: int


class QueryExecutor:
    """Executes queries against the WAPI and post-processes results."""

    def __init__(self, client):
        self._client = client

    def build_params(
        self,
        obj_type: str,
        search_filters: dict,
        default_fields: list[str],
    ) -> QueryParams:
        """Build QueryParams from inputs."""
        return QueryParams(
            obj_type=obj_type,
            search_filters=search_filters,
            return_fields=list(default_fields),
        )

    def execute(self, params: QueryParams) -> QueryResult:
        """Execute the query and apply post-processing."""
        search = dict(params.search_filters)

        records = self._client.get(
            obj_type=params.obj_type,
            search_fields=search,
            return_fields=params.return_fields or None,
        )

        # Client-side sorting (avoids WAPI _sort compatibility issues)
        if params.sort_by:
            records = sorted(records, key=lambda r: r.get(params.sort_by, ""))

        if params.limit and len(records) > params.limit:
            records = records[:params.limit]

        if records:
            # Use actual WAPI key order for columns so headers align with values.
            # The return_fields list controls what the API fetches, not display order.
            fields = list(records[0].keys())
        else:
            fields = []

        return QueryResult(
            records=records,
            fields=fields,
            total_count=len(records),
        )
