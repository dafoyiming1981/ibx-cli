"""WAPI client wrapper around infoblox_client.connector."""

from __future__ import annotations

from typing import Any

from infoblox_client import connector

from ibxcli.core.config import ConnectionConfig
from ibxcli.core.exceptions import IbxAuthError, IbxConnectionError, IbxWapiError


class IbxClient:
    """Thin wrapper around infoblox_client.connector.Connector.

    Provides automatic pagination, return field control, and error translation.
    """

    def __init__(self, config: ConnectionConfig):
        opts = {
            "host": config.host,
            "username": config.username,
            "password": config.password,
            "wapi_version": config.wapi_version,
            "ssl_verify": config.ssl_verify,
        }
        try:
            self._connector = connector.Connector(opts)
        except Exception as e:
            raise IbxConnectionError(f"Failed to initialize connector: {e}")
        self._max_results = config.max_results
        self._timeout = config.timeout

    def get(
        self,
        obj_type: str,
        search_fields: dict | None = None,
        return_fields: list[str] | None = None,
        max_results: int | None = None,
    ) -> list[dict]:
        """Fetch objects from WAPI with automatic pagination."""
        kwargs: dict[str, Any] = {}
        if return_fields:
            kwargs["return_fields"] = return_fields
        kwargs["max_results"] = max_results or self._max_results

        try:
            result = self._connector.get_object(
                obj_type, search_fields or {}, **kwargs
            )
            return result
        except connector.InfobloxConnectionException as e:
            raise IbxConnectionError(f"Connection error: {e}") from e
        except connector.InfobloxException as e:
            err_text = str(e)
            if "401" in err_text or "403" in err_text:
                raise IbxAuthError(
                    f"Authentication failed for {self._connector.host}"
                ) from e
            raise IbxWapiError(code=400, wapi_code="", wapi_text=err_text) from e
        except Exception as e:
            raise IbxConnectionError(f"Unexpected error: {e}") from e

    def raw_get(self, obj_type: str, **kwargs: Any) -> list[dict]:
        """Direct pass-through to connector.get_object for edge cases."""
        search = kwargs.pop("search", {})
        try:
            return self._connector.get_object(obj_type, search, **kwargs)
        except connector.InfobloxException as e:
            raise IbxWapiError(code=400, wapi_text=str(e)) from e

    @property
    def connector(self):
        """Expose the underlying connector for advanced operations."""
        return self._connector
