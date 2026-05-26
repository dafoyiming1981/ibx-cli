"""Infrastructure object handlers."""

from __future__ import annotations

from ibxcli.objects.base import ObjectHandler


class GridHandler(ObjectHandler):
    obj_type = "grid"
    display_name = "Grid"
    default_return_fields = ["name"]

    def build_search_filters(self):
        return {}


class MemberHandler(ObjectHandler):
    obj_type = "member"
    display_name = "Grid Members"
    default_return_fields = ["host_name", "platform", "node_info", "services"]

    def build_search_filters(self, host_name=None, service_state=None):
        filters = {}
        if host_name:
            filters["host_name"] = host_name
        if service_state:
            filters["node_status"] = service_state
        return filters


class DNSViewHandler(ObjectHandler):
    obj_type = "view"
    display_name = "DNS Views"
    default_return_fields = ["name", "network_view", "comment", "is_default"]

    def build_search_filters(self, name=None, network_view=None):
        filters = {}
        if name:
            filters["name"] = name
        if network_view:
            filters["network_view"] = network_view
        return filters


class NetworkViewHandler(ObjectHandler):
    obj_type = "networkview"
    display_name = "Network Views"
    default_return_fields = ["name", "comment", "is_default"]

    def build_search_filters(self, name=None):
        filters = {}
        if name:
            filters["name"] = name
        return filters
