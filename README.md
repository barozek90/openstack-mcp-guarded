# openstack-mcp-guarded

Serwer MCP dla OpenStack z **bezpiecznikami na poziomie serwera** (read-only by default).

Wrapper na [`python-openstackmcp-server`](https://github.com/openstack-kr/python-openstackmcp-server)
(FastMCP + openstacksdk) z middleware polityki: filtrowaniem narzędzi (`tools/list`)
i twardym blokowaniem wywołań (`tools/call`) — niezależnie od klienta MCP
(opencode, Claude Code, itd.).

## Szybki start

```bash
uv sync
uv run pytest          # testy
uv run openstack-mcp-guarded   # serwer (stdio)
```

## Konfiguracja

- Chmury: standardowy `~/.config/openstack/clouds.yaml` (multi-cloud, przełączanie narzędziem `set_cloud_name`)
- Polityka: `~/.config/openstack-mcp-guarded/policy.yaml` (override: env `OS_MCP_GUARD_POLICY`)

```yaml
mode: read-only        # read-only | custom
allow:                 # globy fnmatch, tylko tryb custom
  - "get_*"
  - "set_cloud_name"
deny: []               # wygrywa z allow
```

Pełna dokumentacja: `../openstack-mcp-setup.md`.
