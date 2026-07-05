"""Configuration loading and merging for ibx-cli."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ibxcli.core.exceptions import IbxConfigError

DEFAULT_CONFIG_PATH = Path.home() / ".infoblox" / "config"

DEFAULTS = {
    "host": "",
    "username": "",
    "password": "",
    "wapi_version": "2.13",
    "ssl_verify": True,
    "timeout": 30,
    "max_results": 1000,
    # Vault integration
    "vault_addr": "",
    "vault_cert_path": "",
    "vault_key_path": "",
    "vault_secret_path": "",
    "vault_role_name": "",
    "vault_mount_path": "secret",
    "vault_namespace": "",
}

ENV_MAP = {
    "IBX_HOST": "host",
    "IBX_USERNAME": "username",
    "IBX_PASSWORD": "password",
    "IBX_WAPI_VERSION": "wapi_version",
    "IBX_SSL_VERIFY": "ssl_verify",
    "IBX_TIMEOUT": "timeout",
    "IBX_MAX_RESULTS": "max_results",
    "IBX_VAULT_ADDR": "vault_addr",
    "IBX_VAULT_CERT_PATH": "vault_cert_path",
    "IBX_VAULT_KEY_PATH": "vault_key_path",
    "IBX_VAULT_SECRET_PATH": "vault_secret_path",
    "IBX_VAULT_ROLE_NAME": "vault_role_name",
    "IBX_VAULT_MOUNT_PATH": "vault_mount_path",
    "IBX_VAULT_NAMESPACE": "vault_namespace",
}


@dataclass
class ConnectionConfig:
    """Resolved connection configuration."""

    host: str
    username: str
    password: str
    wapi_version: str = "2.13"
    ssl_verify: bool = True
    timeout: int = 30
    max_results: int = 1000
    # Vault integration (empty string = not using Vault)
    vault_addr: str = ""
    vault_cert_path: str = ""
    vault_key_path: str = ""
    vault_secret_path: str = ""
    vault_role_name: str = ""
    vault_mount_path: str = "secret"
    vault_namespace: str = ""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise IbxConfigError(f"Failed to parse {path}: {e}")


def _merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if v is not None:
            result[k] = v
    return result


def _coerce_types(d: dict) -> dict:
    out = dict(d)
    if isinstance(out.get("ssl_verify"), str):
        out["ssl_verify"] = out["ssl_verify"].lower() in ("true", "1", "yes")
    for key in ("timeout", "max_results"):
        if isinstance(out.get(key), str):
            try:
                out[key] = int(out[key])
            except ValueError:
                pass
    return out


def _is_vault_mode(merged: dict) -> bool:
    """Check if all required Vault env vars are set."""
    return bool(
        merged.get("vault_addr")
        and merged.get("vault_cert_path")
        and merged.get("vault_key_path")
        and merged.get("vault_secret_path")
    )


def load_config(
    config_path: Path | None = None,
    profile: str | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> ConnectionConfig:
    """Load and merge config from file, env, and CLI flags.

    Resolution order (later overrides earlier):
    1. Hardcoded defaults
    2. Config file defaults
    3. Config file profile (if specified)
    4. Environment variables
    5. CLI overrides

    When all four Vault env vars are set (IBX_VAULT_ADDR,
    IBX_VAULT_CERT_PATH, IBX_VAULT_KEY_PATH, IBX_VAULT_SECRET_PATH),
    the password is retrieved from HashiCorp Vault via TLS cert auth.
    """
    cfg_path = config_path or DEFAULT_CONFIG_PATH
    raw = _load_yaml(cfg_path)

    merged = dict(DEFAULTS)

    if "defaults" in raw:
        merged = _merge(merged, raw["defaults"])

    if profile and "profiles" in raw and profile in raw["profiles"]:
        merged = _merge(merged, raw["profiles"][profile])

    for env_key, cfg_key in ENV_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            merged[cfg_key] = val

    if cli_overrides:
        merged = _merge(merged, cli_overrides)

    merged = _coerce_types(merged)

    vault_mode = _is_vault_mode(merged)

    if vault_mode:
        from ibxcli.core.vault import resolve_vault_password

        merged["password"] = resolve_vault_password(
            addr=merged["vault_addr"],
            cert_path=merged["vault_cert_path"],
            key_path=merged["vault_key_path"],
            secret_path=merged["vault_secret_path"],
            role_name=merged.get("vault_role_name") or None,
            mount_path=merged.get("vault_mount_path", "secret"),
            namespace=merged.get("vault_namespace") or None,
        )
    else:
        if not merged["host"]:
            raise IbxConfigError(
                "No Infoblox host configured. "
                "Set --host flag, IBX_HOST env var, or create ~/.infoblox/config"
            )
        if not merged["username"]:
            raise IbxConfigError(
                "No Infoblox username configured. "
                "Set --username flag, IBX_USERNAME env var, or config file"
            )
        # Password can be empty — it will be prompted interactively later

    return ConnectionConfig(
        host=merged["host"],
        username=merged["username"],
        password=merged["password"],
        wapi_version=str(merged["wapi_version"]),
        ssl_verify=bool(merged["ssl_verify"]),
        timeout=int(merged["timeout"]),
        max_results=int(merged["max_results"]),
        vault_addr=merged["vault_addr"],
        vault_cert_path=merged["vault_cert_path"],
        vault_key_path=merged["vault_key_path"],
        vault_secret_path=merged["vault_secret_path"],
        vault_role_name=merged.get("vault_role_name", ""),
        vault_mount_path=merged.get("vault_mount_path", "secret"),
        vault_namespace=merged.get("vault_namespace", ""),
    )
