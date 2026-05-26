"""DHCP object handlers."""

from __future__ import annotations

from ibxcli.objects.base import ObjectHandler


class NetworkHandler(ObjectHandler):
    obj_type = "network"
    display_name = "IPv4 Networks"
    default_return_fields = ["network", "members", "VLAN", "L2", "Zone", "Site"]

    def build_search_filters(self, network=None, network_view=None):
        filters = {}
        if network:
            filters["network"] = network
        if network_view:
            filters["network_view"] = network_view
        return filters


class IPv6NetworkHandler(ObjectHandler):
    obj_type = "ipv6network"
    display_name = "IPv6 Networks"
    default_return_fields = ["ipv6net", "network_view", "comment"]

    def build_search_filters(self, network=None, network_view=None):
        filters = {}
        if network:
            filters["ipv6net"] = network
        if network_view:
            filters["network_view"] = network_view
        return filters


class NetworkContainerHandler(ObjectHandler):
    obj_type = "networkcontainer"
    display_name = "Network Containers"
    default_return_fields = ["network", "network_view", "comment"]

    def build_search_filters(self, network=None, network_view=None):
        filters = {}
        if network:
            filters["network"] = network
        if network_view:
            filters["network_view"] = network_view
        return filters


class FixedAddressHandler(ObjectHandler):
    obj_type = "fixedaddress"
    display_name = "Fixed Addresses"
    default_return_fields = ["ipv4addr", "mac", "name", "network", "network_view", "comment"]

    def build_search_filters(self, ipv4addr=None, mac=None, network_view=None):
        filters = {}
        if ipv4addr:
            filters["ipv4addr"] = ipv4addr
        if mac:
            filters["mac"] = mac
        if network_view:
            filters["network_view"] = network_view
        return filters


class LeaseHandler(ObjectHandler):
    obj_type = "lease"
    display_name = "DHCP Leases"
    default_return_fields = ["address", "binding_state", "client_hostname", "network", "starts", "ends"]

    def build_search_filters(self, address=None, mac=None, network=None, state=None):
        filters = {}
        if address:
            filters["address"] = address
        if mac:
            filters["hardware"] = mac
        if network:
            filters["network"] = network
        if state:
            filters["binding_state"] = state.upper()
        return filters


class IPv4AddressHandler(ObjectHandler):
    obj_type = "ipv4address"
    display_name = "IPv4 Address Usage"
    default_return_fields = ["ip_address", "network", "status", "names", "mac_address"]

    def build_search_filters(self, network=None, status=None, mac=None, name=None):
        filters = {}
        if network:
            filters["network"] = network
        if status:
            filters["status"] = status.upper()
        if mac:
            filters["mac_address"] = mac
        if name:
            filters["names"] = name
        return filters


class RangeHandler(ObjectHandler):
    obj_type = "range"
    display_name = "DHCP Ranges"
    default_return_fields = ["start_addr", "end_addr", "network", "comment", "VLAN", "L2", "Zone", "Site"]

    def build_search_filters(self, network=None, network_view=None):
        filters = {}
        if network:
            filters["network"] = network
        if network_view:
            filters["network_view"] = network_view
        return filters
