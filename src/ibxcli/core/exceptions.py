"""Custom exception hierarchy for ibx-cli."""


class IbxError(Exception):
    """Base exception for all ibx-cli errors."""


class IbxConnectionError(IbxError):
    """Network or connection failure."""


class IbxAuthError(IbxError):
    """Authentication failure (401/403)."""


class IbxWapiError(IbxError):
    """WAPI returned an error response."""

    def __init__(self, code: int, wapi_code: str = "", wapi_text: str = ""):
        super().__init__(wapi_text or f"WAPI error {code}")
        self.code = code
        self.wapi_code = wapi_code
        self.wapi_text = wapi_text


class IbxConfigError(IbxError):
    """Configuration file or value error."""


class IbxFormatError(IbxError):
    """Output formatting error."""
