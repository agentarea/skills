# Integrations: MCP servers, APIs, skills, secrets, files

## Prefer what exists
Before connecting anything new, check `mcp_servers_list` (instances already configured — look at verification status), `openapi_connections_list`, `skills_list`, and the public spec catalog (`mcp_servers_list_specs(search=…)`). Reusing a verified instance avoids duplicate credentials.

## MCP servers
Everything about connecting, configuring, verifying and attaching MCP servers — with exact argument shapes for remote/OAuth, API-key, npx/uvx and docker servers, and how to fix failed verifications — is in `mcp.md`. Read it before creating any MCP spec or instance.

## OpenAPI connections
Turn any HTTP API with an OpenAPI spec into agent tools: `openapi_connections_create(name, base_url, spec_url | spec_content_json, auth_config_id?, custom_headers_json?, url_variables_json?)` → `openapi_connections_discover_tools` → attach as `{"type": "openapi", "settings": {"openapi_connection_id": "<id>"}}`. Several arguments are JSON strings.

## Skills
- Import from GitHub: `skills_import_from_github(github_url)` — a URL to a repo or a folder (`…/tree/main/skills/<name>`). If the repo has several skills you'll get candidates; pick with `skill_name` or `import_all=true`. Limits: ~25 MB repo, 200 files / 10 MB per skill.
- Create inline: `skills_create(files={"SKILL.md": "...", "references/x.md": "..."})`.
- The skill's description decides whether an agent ever activates it — make it specific about when to use it.

## Secrets
- `secrets_list` shows names only. `secrets_create(name, value)` is admin-only and the value passes through the chat — prefer that the user creates it in the web app. Workspace secrets are referenced by id from provider configs, webhooks and MCP OAuth app credentials — but **not** from MCP instance specs: MCP credentials go into the instance itself and are stored as secrets automatically (`mcp.md` §3).
- Never echo secret values back, never put them in agent instructions or run descriptions.

## Workspace files
Shared files agents can read/write. `workspace_files_list`, `workspace_files_get_url` (temporary download link), `workspace_files_upload_urls` (newer; returns upload URLs) and `workspace_files_delete`. For folders, the CLI is easier: `agentarea files sync <dir> [prefix] --workspace <slug>`.

## Clients (exposing AgentArea to outside harnesses)
A client is a governed bundle of MCP instances, platform toolsets and skills behind one endpoint (`<API>/mcp/clients/<id>`) — how a team gives Claude Code / Codex exactly the tools it should have. Attaching things widens what that outside harness can do, so confirm with the user. Tools from attached instances appear as `<prefix>__<tool>`.
