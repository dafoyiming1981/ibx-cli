"""Base class for all NIOS object handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ObjectHandler(ABC):
    """Base class for all NIOS object type handlers."""

    obj_type: str                       # WAPI object type, e.g., "record:a"
    display_name: str                   # Display name, e.g., "A Records"
    default_return_fields: list[str]    # Default fields for table output

    @abstractmethod
    def build_search_filters(self, **kwargs) -> dict:
        """Translate CLI keyword arguments into WAPI search dict."""
        ...
