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

    def _execute_or_queries(
        self,
        params: QueryParams,
        search: dict,
        or_extattr_keys: list[str],
        api_fields: list[str],
    ) -> list[dict]:
        """Execute multiple queries for OR-style extattr filters and merge results.

        For example, *VLAN=100,200 is split into two separate WAPI queries
        (VLAN=100 and VLAN=200), then deduplicated by _ref.

        Multiple OR keys produce a Cartesian product:
        (VLAN=100 OR VLAN=200) AND (Site=BJ1 OR Site=SH1)
        """
        from itertools import product

        # Extract OR values per key
        or_groups: dict[str, list[str]] = {}
        for key in or_extattr_keys:
            or_groups[key] = [v.strip() for v in search.pop(key).split(",")]

        # Base filters (non-OR keys) shared by all queries
        base = dict(search)

        seen_refs: set[str] = set()
        all_records: list[dict] = []

        # Cartesian product across all OR groups
        keys = list(or_groups.keys())
        value_lists = [or_groups[k] for k in keys]
        for combo in product(*value_lists):
            query = dict(base)
            for key, val in zip(keys, combo):
                query[key] = val
            batch = self._client.get(
                obj_type=params.obj_type,
                search_fields=query,
                return_fields=api_fields or None,
            )
            for rec in batch:
                ref = rec.get("_ref", "")
                if ref:
                    if ref not in seen_refs:
                        seen_refs.add(ref)
                        all_records.append(rec)
                else:
                    all_records.append(rec)

        return all_records

    def execute(self, params: QueryParams) -> QueryResult:
        """Execute the query and apply post-processing."""
        search = dict(params.search_filters)

        # Build API return_fields: strip pseudo-fields that require post-processing
        extattr_fields = {"EONID", "VLAN", "L2", "Zone", "Site"}
        has_extattrs = [f for f in (params.return_fields or []) if f in extattr_fields]
        pseudo_fields = {"member_assignment"}
        api_fields = [f for f in params.return_fields if f not in extattr_fields and f not in pseudo_fields] if params.return_fields else []
        if params.return_fields and any(f in pseudo_fields for f in params.return_fields):
            for wf in ("member", "failover_association"):
                if wf not in api_fields:
                    api_fields.append(wf)
        if has_extattrs and api_fields and "extattrs" not in api_fields:
            api_fields.append("extattrs")

        # Detect OR-style extattr filters (e.g. *VLAN -> "100,200" means VLAN=100 OR VLAN=200)
        or_extattr_keys = [k for k, v in search.items() if k.startswith("*") and "," in v]
        if or_extattr_keys:
            records = self._execute_or_queries(params, search, or_extattr_keys, api_fields)
        else:
            import sys
            print(f"[DEBUG] search_fields: {search}", file=sys.stderr)
            records = self._client.get(
                obj_type=params.obj_type,
                search_fields=search,
                return_fields=api_fields or None,
            )
            print(f"[DEBUG] records count: {len(records) if records else 0}", file=sys.stderr)

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
            # Flatten members to short hostnames for display
            members = record.get("members")
            if isinstance(members, list):
                names = []
                for m in members:
                    if isinstance(m, str):
                        short = m
                    elif isinstance(m, dict):
                        short = m.get("name") or m.get("host_name") or m.get("_ref", "")
                    else:
                        continue
                    names.append(short.split(".")[0])
                record["members"] = ", ".join(names) if names else ""
            # Flatten range member assignment to short hostname
            member = record.get("member")
            if isinstance(member, dict):
                short = member.get("name") or member.get("host_name", "")
                record["member"] = short.split(".")[0] if short else ""
            # Compute member_assignment display value
            assoc_type = record.get("server_association_type", "NONE")
            if assoc_type == "MEMBER":
                record["member_assignment"] = record.get("member", "")
            elif assoc_type == "FAILOVER":
                record["member_assignment"] = record.get("failover_association", "")
            else:
                record["member_assignment"] = "None"

        # For range objects, inherit VLAN/Zone/Site extattrs from parent network
        if params.obj_type == "range":
            net_ea_fields = [f for f in extattr_fields if f in ("VLAN", "Zone", "Site")]
            # Check if any range is missing these fields
            needs_inheritance = any(
                not record.get(f) for record in records for f in net_ea_fields
            )
            if needs_inheritance and net_ea_fields:
                # Collect unique network CIDRs from ranges
                net_cidrs = set()
                for record in records:
                    cidr = record.get("network", "")
                    if cidr:
                        net_cidrs.add(cidr)

                # Fetch parent networks with extattrs
                network_extattrs = {}
                if net_cidrs:
                    for cidr in net_cidrs:
                        net_records = self._client.get(
                            obj_type="network",
                            search_fields={"network": cidr},
                            return_fields=["network", "extattrs"],
                        )
                        for nr in net_records:
                            ext = nr.get("extattrs", {})
                            network_extattrs[cidr] = {
                                f: ext.get(f, {}).get("value", "")
                                for f in net_ea_fields
                            }

                # Inherit missing extattrs from parent network
                for record in records:
                    cidr = record.get("network", "")
                    parent_ea = network_extattrs.get(cidr, {})
                    for f in net_ea_fields:
                        if not record.get(f):
                            record[f] = parent_ea.get(f, "")

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
