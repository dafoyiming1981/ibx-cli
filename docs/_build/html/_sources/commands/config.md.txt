# Config Commands

:::{note}
The `config` command group manages local connection configuration and provides connection testing.
:::

## `ibx config init`

Create a sample config file at `~/.infoblox/config`.

```bash
ibx config init
```

This generates a YAML configuration with `defaults` and `profiles` sections.

## `ibx config show`

Display the currently resolved configuration (password is masked).

```bash
ibx config show
```

Output includes host, username, WAPI version, SSL verification, timeout, and max results.

## `ibx config test-connection`

Test connectivity to the Infoblox Grid Master.

```bash
ibx config test-connection
ibx --host 10.0.0.2 --username admin --password secret config test-connection
```

Successful output:

```
Connecting to 10.x.x.x...
Connected successfully!
  Grid: infoblox-grid
  WAPI version: 2.13
```

## Related Commands

- [DNS Commands](dns.md)
- [DHCP Commands](dhcp.md)
- [Infrastructure Commands](infra.md)
- [Search](search.md)
