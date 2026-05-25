"""DNS object handlers."""

from __future__ import annotations

from ibxcli.objects.base import ObjectHandler


class AuthZoneHandler(ObjectHandler):
    obj_type = "zone_auth"
    display_name = "Authoritative Zones"
    default_return_fields = ["fqdn", "view", "zone_format", "comment", "eonid"]

    def build_search_filters(self, view=None, fqdn=None, regex=False):
        filters = {}
        if view:
            filters["view"] = view
        if fqdn:
            filters["fqdn~" if regex else "fqdn"] = fqdn
        return filters


class ARecordHandler(ObjectHandler):
    obj_type = "record:a"
    display_name = "A Records"
    default_return_fields = ["name", "ipv4addr", "view", "zone", "ttl", "comment", "eonid"]

    def build_search_filters(self, name=None, ipv4addr=None, zone=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if ipv4addr:
            filters["ipv4addr"] = ipv4addr
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        return filters


class AAAARecordHandler(ObjectHandler):
    obj_type = "record:aaaa"
    display_name = "AAAA Records"
    default_return_fields = ["name", "ipv6addr", "view", "zone", "ttl", "comment", "eonid"]

    def build_search_filters(self, name=None, ipv6addr=None, zone=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if ipv6addr:
            filters["ipv6addr"] = ipv6addr
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        return filters


class CNAMERecordHandler(ObjectHandler):
    obj_type = "record:cname"
    display_name = "CNAME Records"
    default_return_fields = ["name", "canonical", "view", "zone", "ttl", "comment", "eonid"]

    def build_search_filters(self, name=None, canonical=None, zone=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if canonical:
            filters["canonical"] = canonical
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        return filters


class MXRecordHandler(ObjectHandler):
    obj_type = "record:mx"
    display_name = "MX Records"
    default_return_fields = ["name", "mail_exchanger", "preference", "view", "zone", "ttl", "eonid"]

    def build_search_filters(self, name=None, zone=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        return filters


class NSRecordHandler(ObjectHandler):
    obj_type = "record:ns"
    display_name = "NS Records"
    default_return_fields = ["name", "nameserver", "view", "zone", "ttl", "eonid"]

    def build_search_filters(self, name=None, zone=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        return filters


class TXTRecordHandler(ObjectHandler):
    obj_type = "record:txt"
    display_name = "TXT Records"
    default_return_fields = ["name", "text", "view", "zone", "ttl", "comment", "eonid"]

    def build_search_filters(self, name=None, zone=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        return filters


class PTRRecordHandler(ObjectHandler):
    obj_type = "record:ptr"
    display_name = "PTR Records"
    default_return_fields = ["name", "ptrdname", "ipv4addr", "ipv6addr", "view", "zone", "ttl", "eonid"]

    def build_search_filters(self, name=None, ipv4addr=None, ipv6addr=None, zone=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if ipv4addr:
            filters["ipv4addr"] = ipv4addr
        if ipv6addr:
            filters["ipv6addr"] = ipv6addr
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        return filters


class HostRecordHandler(ObjectHandler):
    obj_type = "record:host"
    display_name = "Host Records"
    default_return_fields = ["name", "ipv4addrs", "view", "comment", "eonid"]

    def build_search_filters(self, name=None, ipv4addr=None, mac=None, view=None, regex=False):
        filters = {}
        if name:
            filters["name~" if regex else "name"] = name
        if ipv4addr:
            filters["ipv4addr"] = ipv4addr
        if mac:
            filters["mac"] = mac
        if view:
            filters["view"] = view
        return filters


class AllRecordsHandler(ObjectHandler):
    obj_type = "allrecords"
    display_name = "All Records"
    default_return_fields = ["name", "type", "address", "view", "zone", "ttl", "eonid"]

    def build_search_filters(self, zone=None, view=None, type=None, regex=False):
        filters = {}
        if zone:
            filters["zone"] = zone
        if view:
            filters["view"] = view
        if type:
            filters["type"] = type
        return filters
