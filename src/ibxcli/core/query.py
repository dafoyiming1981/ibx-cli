"""Query execution engine for ibx-cli."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QueryParams:
    """Parameters for a single WAPI query."""

    obj_type: str
    search_filters: dict = field(default_factory=dict)
    return_fields: list[str] = field(default_factory=list)
    limit: int | None = None
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

        # Build API return_fields: strip pseudo-fields that require post-processing
        # EONID, VLAN, L2, ZONE are extensible attributes, not WAPI fields
        extattr_fields = {"EONID", "VLAN", "L2", "Zone", "Site"}
        has_extattrs = [f for f in (params.return_fields or []) if f in extattr_fields]
        api_fields = [f for f in params.return_fields if f not in extattr_fields] if params.return_fields else []
        if has_extattrs and api_fields and "extattrs" not in api_fields:
            api_fields.append("extattrs")

        records = self._client.get(
            obj_type=params.obj_type,
            search_fields=search,
            return_fields=api_fields or None,
        )

        # Post-process: extract extensible attributes, remove _ref and extattrs
        for record in records:
            if has_extattrs:
                extattrs = record.pop("extattrs", None)
                for ea_key in has_extattrs:
                    if extattrs and ea_key in extattrs:
                        record[ea_key] = extattrs[ea_key].get("value", "")
                    else:
                        record[ea_key] = ""
            record.pop("_ref", None)
            # Flatten ipv4addrs: [{"_ref": "...", "ipv4addr": "10.0.0.1", ...}] → ["10.0.0.1"]
            ipv4addrs = record.get("ipv4addrs")
            if isinstance(ipv4addrs, list) and ipv4addrs and isinstance(ipv4addrs[0], dict):
                record["ipv4addrs"] = [a.get("ipv4addr", "") for a in ipv4addrs]
            # Flatten members to comma-separated hostnames for display
            members = record.get("members")
            if isinstance(members, list):
                names = []
                for m in members:
                    if isinstance(m, str):
                        names.append(m)
                    elif isinstance(m, dict):
                        names.append(
                            m.get("name") or m.get("host_name") or m.get("_ref", "")
                        )
                record["members"] = ", ".join(names) if names else ""

        # Client-side sorting (avoids WAPI _sort compatibility issues)
        if params.sort_by:
            records = sorted(records, key=lambda r: r.get(params.sort_by, ""))

        if params.limit and len(records) > params.limit:
            records = records[:params.limit]

        # Build display fields from handler defaults, removing _ref
        if params.return_fields:
            fields = [f for f in params.return_fields if f != "_ref"]
            for ea_key in has_extattrs:
                if ea_key not in fields:
                    fields.append(ea_key)
            if "node_info" in fields:
                fields.remove("node_info")
        elif records:
            fields = list(records[0].keys())
        else:
            fields = []

        return QueryResult(
            records=records,
            fields=fields,
            total_count=len(records),
        )
