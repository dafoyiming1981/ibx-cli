# ibx-cli Documentation

Infoblox NIOS CLI toolset for DNS/DHCP management via WAPI.

```
CLI (click) → ObjectHandler → QueryExecutor → IbxClient → infoblox_client → WAPI
```

## Quick Start

### Installation

**Via git + pip:**

```bash
git clone https://github.com/dafoyiming1981/ibx-cli.git
cd ibx-cli
pip3.12 install --user -e .
```

**Via install script:**

```bash
bash install_ibxcli.sh
echo 'alias ibx="$HOME/.local/bin/ibx"' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
ibx --version
```

### Configuration

```bash
ibx config init
vi ~/.infoblox/config
chmod 600 ~/.infoblox/config
```

Example config:

```yaml
defaults:
  host: 10.x.x.x
  username: admin
  password: your_password
  wapi_version: "2.13"
  ssl_verify: false
  timeout: 30
  max_results: 1000

profiles:
  prod:
    host: infoblox-prod.example.com
  lab:
    host: infoblox-lab.example.com
```

### CLI Usage

```bash
ibx config test-connection
ibx dns zones
ibx dhcp networks
```

## Why ibx-cli

```{toctree}
:maxdepth: 1

why-ibxcli
```

## Command Reference

```{toctree}
:maxdepth: 2
:caption: Commands

commands/config
commands/dns
commands/dhcp
commands/infra
commands/search
```

## Architecture

```{toctree}
:maxdepth: 2
:caption: Architecture

api
```

## Indices and Tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
