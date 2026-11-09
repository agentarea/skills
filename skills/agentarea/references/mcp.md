# Setting up MCP servers

Read this whenever the user asks to connect, add, set up or fix an MCP server / integration (GitHub, Slack, Linear, Notion, Jira, a database, an internal API, "an MCP from this repo", …).

## The decision, in order

1. **Already there?** `mcp_servers_list` — an instance for this service with `verification.status == "succeeded"` → just attach it (§6). A failed one → fix it (§5) rather than creating a duplicate.
2. **In the catalog?** `mcp_servers_list_specs(search="<service>")` — leave `is_public` at its default (`false`); `is_public=true` *hides* the built-in catalog. The catalog has ~95 ready remote servers (GitHub, Notion, Slack, Linear, Atlassian, Sentry, Stripe, Vercel, …). `mcp_servers_get_spec(id)` shows which values (`env_schema`) it needs. Prefer a catalog spec: the URL and transport are already right.
3. **Otherwise build a spec** — pick the recipe by how the server is delivered:
   - a hosted URL (`https://…/mcp` or `…/sse`) → remote (§2a/§2b)
   - an npm / PyPI package run with `npx` / `uvx` → command (§2c)
   - a container image that serves HTTP → docker (§2d)
4. **Create the instance** with the credentials, **verify**, **confirm success**, then **attach**.

Ask the user only for what you can't find: which service/account, and credentials (or that they'll complete OAuth in the browser).

## 1. Shapes you must get right

- Arguments ending in `_json` are **JSON encoded as a string**: `env_schema_json='[{"name":"X","isSecret":true}]'`, `cmd_json='["npx","-y","pkg"]'`, `json_spec_json='{"environment":{"X":"v"}}'`. Empty string = not set.
- **Spec** (`mcp_servers_create_spec`) = how to reach/run the server. **Instance** (`mcp_servers_create`) = this workspace's configured copy; `server_spec_id` and `json_spec_json` are required (`"{}"` is fine).
- The transport is decided once, on the spec: `json_spec.type` if given, else `remote_url` → url, else `cmd_json` → command, else `docker_image_url` → docker. Don't set `cmd_json` together with `docker_image_url` — it becomes a command server and ignores the image.
- In the **instance** `json_spec`, only these keys matter: `environment` (env vars for command/docker), `headers` (HTTP headers for remote), `env_vars` (names to force into the secret store), `port` (docker, create-only). Transport keys (`type`, `endpoint_url`, `image`, `command`, `args`) are stripped on create and rejected on update.
- `env_schema` entries: `{"name": "...", "description": "...", "isSecret": true|false, "isRequired": true|false, "default": "..." (non-secret only)}`. It classifies values; it does not enforce them — a missing required value shows up as a failed verification.

## 2. Recipes

### 2a. Remote server with OAuth (Linear, Notion, GitHub, Atlassian, …)
Prefer the catalog spec. By hand:
```
mcp_servers_create_spec(
  name="Linear", description="Linear issues",
  remote_url="https://mcp.linear.app/mcp",
  json_spec_json='{"remotes":[{"type":"streamable-http","url":"https://mcp.linear.app/mcp"}]}')
mcp_servers_create(name="Linear", server_spec_id="<spec id>", json_spec_json="{}")
```
- Declaring `remotes[].type` (`streamable-http` or `sse`) avoids URL guessing.
- Don't add an `Authorization` header (not even empty) — an instance with any headers won't use its OAuth token.
- Right after create, verification is expected to fail or tools return 401: there is no token yet. **OAuth must be done by the user in a browser** — no MCP tool can do it. Send them to `https://app.agentarea.ai/w/<workspace>/connections/<instance_id>` → **Connect**. Some providers (GitHub, Google) need an OAuth app: the page then asks for a client ID/secret; the app's redirect URI must be `<API>/v1/mcp-oauth/callback`. When they're done, verify (§4).

### 2b. Remote server with an API key / token header
```
mcp_servers_create_spec(
  name="Vendor Search", description="…",
  remote_url="https://mcp.vendor.com/mcp",
  env_schema_json='[{"name":"Authorization","description":"Bearer token","isSecret":true}]',
  json_spec_json='{"remotes":[{"type":"streamable-http","url":"https://mcp.vendor.com/mcp"}]}')
mcp_servers_create(name="Vendor Search", server_spec_id="<id>",
  json_spec_json='{"headers":{"Authorization":"Bearer <token>"}}')
```
- The header value is sent literally — include the `Bearer ` prefix if the server expects it. Use the header name the vendor documents (`X-API-Key` is not interchangeable with `Authorization`).
- GitHub with a personal access token: `remote_url="https://api.githubcopilot.com/mcp/"` (trailing slash) + `Authorization: Bearer ghp_…`.

### 2c. npx / uvx package (stdio servers)
```
mcp_servers_create_spec(
  name="GitHub (npx)", description="GitHub via npx",
  cmd_json='["npx","-y","@modelcontextprotocol/server-github"]',
  env_schema_json='[{"name":"GITHUB_PERSONAL_ACCESS_TOKEN","description":"GitHub PAT","isSecret":true,"isRequired":true}]')
mcp_servers_create(name="GitHub (npx)", server_spec_id="<id>",
  json_spec_json='{"environment":{"GITHUB_PERSONAL_ACCESS_TOKEN":"<token>"}}')
```
- Python: `cmd_json='["uvx","mcp-server-fetch"]'`.
- Runs on AgentArea's base image (Node 22, uv/uvx, Python 3.12, git) behind an HTTP bridge — don't set `docker_image_url` or `port`. The first start downloads the package and can take minutes; verification waits.
- Packages needing other runtimes or system libraries won't start.

### 2d. Docker image (must speak HTTP)
```
mcp_servers_create_spec(
  name="Filesystem", description="…",
  docker_image_url="mcp/filesystem:latest",
  json_spec_json='{"port":8000,"args":["/data"]}',
  env_schema_json='[{"name":"ALLOWED_DIRECTORIES","isSecret":false}]')
mcp_servers_create(name="Filesystem", server_spec_id="<id>",
  json_spec_json='{"environment":{"ALLOWED_DIRECTORIES":"/data"}}')
```
- The container must serve **Streamable HTTP at `:<port>/mcp`** (default 8000). A stdio-only image will hang until `list_tools_timeout` — run it as a command (§2c) instead, or build it `FROM agentarea/agentarea-mcp-base`.
- Container args go in the spec's `json_spec_json` as `"args"`, not `cmd_json`.
- Containers run as non-root with a read-only filesystem (writable `/tmp` only) and can reach only the public internet — no private/intranet addresses.

## 3. Credentials
- Any value in instance `environment` or `headers` that is `isSecret` in `env_schema`, **or not declared in `env_schema` at all**, is moved into the secret store automatically and never returned. Non-secret declared values stay visible.
- Values pass through the chat when you put them in tool arguments. Offer the alternative: create the instance without the secret and let the user paste it on the instance page in the web app.
- Never send back a masked `******` value — it's a no-op that keeps the old value, and it does not set a new one.
- Workspace secrets created with `secrets_create` are **not** referenced by MCP instance specs; give the value in the instance (or via the web app).

## 4. Verify — and actually check it
`mcp_servers_verify(instance_id)` blocks until a result (cold containers: up to ~10 minutes). Then confirm `verification.status == "succeeded"` and that `tools` is non-empty (`mcp_servers_get`). **Agents silently get no tools from an instance that hasn't verified successfully**, so never attach and move on without checking. Show the user the discovered tool names — they need them for `allowed_tools`.

## 5. When verification fails
| `verification.error.code` | Likely cause → fix |
|---|---|
| `mcp_error` (remote: "Could not connect to the MCP server") | Wrong URL/transport, or auth rejected (401 is masked as a connect failure). Check the exact canonical URL (root vs `/mcp` vs `/sse`, trailing slash), declare `remotes[].type`, check header name/value, or complete OAuth. |
| `oauth_reauth_required` | Token expired/revoked → user reconnects on the instance page. |
| `container_failed` | Missing required env var, bad value, image needs root/writable FS, wrong architecture. |
| `list_tools_timeout` | Not an MCP server, or a stdio image configured as docker → use a command spec. |
| "Endpoint URL is not an allowed address" | Private/loopback/intranet host — not reachable from the cloud. |
| stuck `in_progress` | Run verify again. |

To change credentials: `mcp_servers_update(instance_id, json_spec_json='{"environment":{…}}' or '{"headers":{…}}')` then verify again. You can't change the transport/URL/command on an instance — fix the spec (`mcp_servers_update_spec`, for workspace specs; catalog specs are read-only) or create a new instance. Tool lists are a snapshot; verify again after the server changes.

## 6. Attach to an agent
Tool entry:
```json
{"type": "mcp", "name": "<instance id>", "settings": {"allowed_tools": ["list_issues", "create_issue"]}}
```
- `allowed_tools`: omit or `null` = **all** tools; `[]` = **none**; otherwise the raw tool names from `tools`. Items may also be `{"tool_name": "create_issue", "requires_user_confirmation": true}` — that turns into an approval rule for that tool.
- **New agent:** include it in `agents_create(tools=[…])`. If the server's `agents_create` has no `tools` parameter (older deployments), create the agent via REST `POST /v1/workspaces/<ws>/agents` with `"tools"`, or create it and add tools in the web app.
- **Existing agent:** there is no MCP tool for this (`agents_update` can't change tools, `agents_get` doesn't show them). Use the web app agent editor, or REST `PATCH /v1/workspaces/<ws>/agents/<id>` with the **full** `tools` list (it replaces the list — read the current one via REST `GET` first).
- `projects_add_mcp_instance` only groups the instance under a project; it does **not** give any agent its tools.
- For an outside harness (Claude Code, Codex) use a client: `clients_add_mcp_instance` (privileged — confirm).
- At run time the agent sees tools as `mcp__<instance name>__<tool>`; policies can target them.

## 7. Report back
Tell the user: what you created (spec/instance names and ids), whether verification succeeded and the tools found, what they still need to do (OAuth Connect, paste a secret, attach in the web app), and which agent(s) can now use it.
