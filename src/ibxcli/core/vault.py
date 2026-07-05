"""HashiCorp Vault integration for credential retrieval.

Uses TLS client certificate authentication to retrieve secrets
from Vault without storing passwords on disk.
"""

from __future__ import annotations

from pathlib import Path

import requests

from ibxcli.core.exceptions import IbxConfigError


def _validate_file(path: str, label: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_file():
        raise IbxConfigError(f"{label} file not found: {p}")
    return p


def resolve_vault_password(
    addr: str,
    cert_path: str,
    key_path: str,
    secret_path: str,
    role_name: str | None = None,
    mount_path: str = "secret",
    namespace: str | None = None,
    ssl_verify: bool = True,
) -> str:
    """Authenticate to Vault via TLS cert and retrieve the Infoblox password.

    Args:
        addr: Vault server address (e.g. https://vault.example.com:8200).
        cert_path: Path to TLS client certificate file.
        key_path: Path to TLS client private key file.
        secret_path: KV v2 secret path (e.g. infoblox/prod).
        role_name: Optional cert auth role name. Defaults to certificate CN.
        mount_path: Vault secret engine mount path (default: "secret").
        namespace: Optional Vault enterprise namespace.

    Returns:
        The password string retrieved from Vault.

    Raises:
        IbxConfigError: On connection failure, auth failure, or secret not found.
    """
    cert_file = _validate_file(cert_path, "TLS cert")
    key_file = _validate_file(key_path, "TLS key")

    session = requests.Session()
    session.cert = (str(cert_file), str(key_file))
    session.verify = ssl_verify

    # Shared headers
    headers = {}
    if namespace:
        headers["X-Vault-Namespace"] = namespace

    # Step 1: Authenticate via cert login (JSON body, matching curl --data)
    login_url = f"{addr.rstrip('/')}/v1/auth/cert/login"
    login_body = {}
    if role_name:
        login_body["name"] = role_name

    try:
        resp = session.post(login_url, json=login_body, headers=headers, timeout=30)
    except requests.exceptions.SSLError as e:
        raise IbxConfigError(
            f"Vault SSL error: {e}. "
            f"If using a self-signed cert, set IBX_VAULT_SSL_VERIFY=false. "
            f"(ssl_verify={ssl_verify})"
        ) from e
    except requests.RequestException as e:
        raise IbxConfigError(f"Vault connection failed: {e}") from e

    if resp.status_code != 200:
        raise IbxConfigError(
            f"Vault cert authentication failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        body = resp.json()
    except ValueError as e:
        raise IbxConfigError(f"Vault returned invalid JSON: {resp.text[:200]}") from e

    token = body.get("auth", {}).get("client_token")
    if not token:
        raise IbxConfigError("Vault did not return a client token")

    # Step 2: Read secret from KV v2
    secret_url = f"{addr.rstrip('/')}/v1/{mount_path}/data/{secret_path.lstrip('/')}"
    headers["X-Vault-Token"] = token

    try:
        resp = session.get(secret_url, headers=headers, timeout=30)
    except requests.exceptions.SSLError as e:
        raise IbxConfigError(
            f"Vault SSL error reading secret: {e}. "
            f"If using a self-signed cert, set IBX_VAULT_SSL_VERIFY=false. "
            f"(ssl_verify={ssl_verify})"
        ) from e
    except requests.RequestException as e:
        raise IbxConfigError(f"Vault secret read failed: {e}") from e

    if resp.status_code == 403:
        raise IbxConfigError(
            f"Vault permission denied for secret path: {secret_path}"
        )
    if resp.status_code == 404:
        raise IbxConfigError(
            f"Vault secret not found at path: {secret_path}"
        )
    if resp.status_code != 200:
        raise IbxConfigError(
            f"Vault secret read failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        body = resp.json()
    except ValueError as e:
        raise IbxConfigError(f"Vault returned invalid JSON: {resp.text[:200]}") from e

    # KV v2 structure: {"data": {"data": {"password": "...", ...}}}
    password = body.get("data", {}).get("data", {}).get("password")
    if not password:
        raise IbxConfigError(
            f"No 'password' field found in Vault secret at {secret_path}"
        )

    return password
