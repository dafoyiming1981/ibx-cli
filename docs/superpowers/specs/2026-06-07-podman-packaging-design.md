# Podman Container + Windows venv Packaging Design

## Overview

Package ibx-cli for two deployment targets:
1. **Linux**: Rootless Podman container, pushed to company Artifactory for vulnerability scanning
2. **Windows**: PowerShell venv install script for direct local use

## Linux: Podman Container

### Containerfile
- Base image: company-provided Linux base image (user has one available)
- Install Python 3.12 + pip from base image repos
- Copy wheel from `dist/ibx_cli-*.whl` and install via pip
- Set `ENTRYPOINT ["ibx"]` so `podman run <image> dns zones` works directly
- Non-root user inside container: `ibx` (UID 1000)

### Build & Push Flow
1. `python3 -m build` — generate wheel in `dist/`
2. `podman build -t artifactory.company.com/ibx-cli:0.1.0 -f Containerfile .`
3. `podman push artifactory.company.com/ibx-cli:0.1.0`

Automated via `scripts/build_and_push.sh` — accepts image tag as argument.

### Containerfile Location
- Root of repo: `Containerfile`

### Running the Container
```bash
# Volume mount (primary)
podman run --rm -v ~/.infoblox/config:/home/ibx/.infoblox/config:Z \
  artifactory.company.com/ibx-cli:0.1.0 dns zones

# Environment variables (quick test)
podman run --rm \
  -e IBX_HOST=10.0.0.2 -e IBX_USERNAME=admin -e IBX_PASSWORD=secret \
  artifactory.company.com/ibx-cli:0.1.0 dns a

# Debug shell
podman run --rm -it --entrypoint /bin/sh artifactory.company.com/ibx-cli:0.1.0
```

### Network
- Container has network access to Infoblox WAPI (no extra config needed)
- No port mapping required (CLI only, no server)

## Windows: venv Install

### PowerShell Script
`scripts/install_windows.ps1` — runs on Windows:
1. Check Python 3.12 availability, fail with clear message if missing
2. Create `~/ibx-env` venv
3. Install wheel from `dist/` or clone repo and `pip install -e .`
4. Add `ibx` to PATH via shell profile (optional)

### Usage
```powershell
.\scripts\install_windows.ps1
ibx --version
ibx dns zones
```

Config file at `%USERPROFILE%\.infoblox\config` works natively.

## Files to Create
- `Containerfile` — Podman build definition
- `scripts/build_and_push.sh` — Linux build + push automation
- `scripts/install_windows.ps1` — Windows venv installer
- `README.md` — update with container and Windows install sections
