"""Object handler registry."""

from ibxcli.objects.base import ObjectHandler
from ibxcli.objects.dns import (
    ARecordHandler, AAAARecordHandler, AllRecordsHandler, AuthZoneHandler,
    CNAMERecordHandler, HostRecordHandler, MXRecordHandler, NSRecordHandler,
    PTRRecordHandler, TXTRecordHandler,
)
from ibxcli.objects.dhcp import (
    FixedAddressHandler, IPv4AddressHandler, IPv6NetworkHandler,
    LeaseHandler, NetworkContainerHandler, NetworkHandler,
)
from ibxcli.objects.infra import (
    DNSViewHandler, GridHandler, MemberHandler, NetworkViewHandler,
)

HANDLERS: dict[str, ObjectHandler] = {
    # DNS
    "zone:auth": AuthZoneHandler(),
    "record:a": ARecordHandler(),
    "record:aaaa": AAAARecordHandler(),
    "record:cname": CNAMERecordHandler(),
    "record:mx": MXRecordHandler(),
    "record:ns": NSRecordHandler(),
    "record:txt": TXTRecordHandler(),
    "record:ptr": PTRRecordHandler(),
    "record:host": HostRecordHandler(),
    "allrecords": AllRecordsHandler(),
    # DHCP
    "network": NetworkHandler(),
    "ipv6network": IPv6NetworkHandler(),
    "networkcontainer": NetworkContainerHandler(),
    "fixedaddress": FixedAddressHandler(),
    "lease": LeaseHandler(),
    "ipv4address": IPv4AddressHandler(),
    # Infrastructure
    "grid": GridHandler(),
    "member": MemberHandler(),
    "view": DNSViewHandler(),
    "networkview": NetworkViewHandler(),
}
