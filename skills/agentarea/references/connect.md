# Connecting to AgentArea

The cloud is **agentarea.ai** (web app `app.agentarea.ai`, API `api.agentarea.ai`). Self-hosted installs use their own API URL; ask for it if the user isn't on the cloud.

## MCP endpoints
| Endpoint | Use |
|---|---|
| `https://api.agentarea.ai/mcp` | All the user's workspaces; tools take a `workspace` argument; `workspaces_list` available. Good default. |
| `https://api.agentarea.ai/mcp/w/<workspace>` | Pinned to one workspace; smaller tool list, can't act in the wrong workspace. Good for a team or a single project. |
| `…/mcp/clients/<client_id>` | A curated bundle an admin set up (specific MCP servers, toolsets, skills). |

Add `?toolsets=runs,agents,inbox` (comma-separated) to expose only some toolsets. An unknown toolset name is an error. A 403 on a pinned URL means the workspace doesn't exist *or* the user isn't a member.

## Claude Code
Easiest — install the plugin, which adds both this skill and the MCP server:
```
/plugin marketplace add agentarea/skills
/plugin install agentarea@agentarea        # agentarea.ai
```
Then run `/mcp`, pick `agentarea`, and log in in the browser (OAuth). No API key needed.

Manual alternative:
```
claude mcp add --transport http agentarea https://api.agentarea.ai/mcp
```
then `/mcp` to log in. For a pinned workspace use `…/mcp/w/<workspace>`.

With an API key instead of OAuth (CI, headless):
```
claude mcp add --transport http agentarea "https://api.agentarea.ai/mcp/w/<workspace>" \
  --header "Authorization: Bearer $AGENTAREA_TOKEN"
```

## Claude (web / desktop)
Settings → Connectors → Add custom connector → URL `https://api.agentarea.ai/mcp` → Connect, and log in. Upload this skill via Settings → Capabilities → Skills.

## Codex and other harnesses
Any client that speaks streamable-HTTP MCP with OAuth works with the same URL. The AgentArea CLI can set it up:
```
npm install -g @agentarea/cli
agentarea login --api-url=https://api.agentarea.ai
agentarea workspace use <slug>
agentarea connect codex      # or: agentarea connect claude
```
If an admin created a client for the team, `agentarea mcp sync --client=<id> --target=codex|claude` installs exactly that bundle.

## API keys
Created by a member in the web app (or `POST /v1/workspaces/<ws>/api-keys/`). The `aat_…` token is shown once. A key carries its creator's full access to the workspace — there is no read-only key — so treat it like a password, set an expiry, and rotate by creating a new key then revoking the old one. Using a client endpoint additionally requires permission on that client.

## Troubleshooting
- **401** — not logged in / token expired: run `/mcp` and re-authenticate.
- **403 on a pinned URL** — wrong workspace slug or not a member.
- **A tool is missing** — the URL filters toolsets, the user lacks the role, or the server predates the tool.
- **"Not authorized for this client"** — ask the client's owner for access.
