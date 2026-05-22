"""Formatter base class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseFormatter(ABC):
    """Output formatter interface."""

    @abstractmethod
    def render(self, records: list[dict], fields: list[str] | None) -> str:
        """Render records to a string."""


FORMATTERS: dict[str, type[BaseFormatter]] = {}


def register_formatter(name: str):
    """Decorator to register a formatter class."""
    def wrapper(cls):
        FORMATTERS[name] = cls
        return cls
    return wrapper


def get_formatter(name: str) -> BaseFormatter:
    """Get a formatter instance by name."""
    from ibxcli.formatters import table, json_fmt, csv_fmt  # noqa: F401
    cls = FORMATTERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown format: {name}")
    return cls()
