# Agents and models

## What an agent is
A stored definition, not a running process:

| Field | Meaning |
|---|---|
| `name`, `description` | Shown in the UI and to other agents. |
| `instruction` | The agent's job description (system prompt). Keep it under ~5,000 characters. |
| `model_id` | A **model instance id** (`models_list_instances`), not a model name. |
| `tools` | Typed list of capability entries (below). Required on create; `[]` is fine. |
| `skills` | Skill ids the agent can activate. |

Each run of an agent is a separate execution with its own budget and event log.

## Writing a good instruction
Write it like onboarding a new hire: role and goal, the inputs it will get, what a good result looks like (format, length, where to put it), which tools to use for what, what to do when information is missing (ask via input request vs. make a reasonable assumption), and what it must never do. Specific beats long.

## Tool entries
`tools` is a list of objects discriminated by `type`:

```json
{"type": "mcp", "name": "<mcp instance id>", "settings": {"allowed_tools": ["search", "create_issue"]}}
{"type": "openapi", "name": "<label>", "settings": {"openapi_connection_id": "<id>"}}
{"type": "code", "name": "agentarea/shell"}
{"type": "agent", "name": "<agent id>"}
```

- `mcp.name` is the **instance** id, not the spec. `allowed_tools`: omitted/`null` = all tools, `[]` = **none**, or a list of raw tool names (items may be `{"tool_name": …, "requires_user_confirmation": true}`). Restrict to what the job needs.
- Configured tools are candidates, not permissions — policies decide what may run, and some calls may require approval.
- An MCP instance must have a **successful** verification; otherwise the agent silently gets none of its tools. See `mcp.md`.
- Some deployments' `agents_create` has no `tools` parameter yet — then create via REST `POST /v1/workspaces/<ws>/agents` with `tools`, or add tools in the web app.

## Changing tools or skills on an existing agent
`agents_update` cannot change `tools` or `skills`, and `agents_get` does not show tools. Options:
- The web app's agent editor.
- REST `PATCH /v1/workspaces/<ws>/agents/<id>` with `tools` and/or `skill_ids` — both **replace** the whole list, so read the current list with REST `GET` first and send the full desired set.
- Note: `projects_add_mcp_instance` does not give agents tools; it only groups.
- For a fresh agent, simply create it with the right tools.

Tell the user which route you are taking.

## Skills on agents
A skill is a folder with `SKILL.md`. The agent sees each skill's name and description and activates it when relevant, so the description decides whether it is ever used. Get skills from: an existing workspace skill, `skills_import_from_github`, `skills_create`, or the catalog. Attach via `skill_ids` (replaces the set) or add to a project.

## Model layers
- **Catalog**: provider spec → model spec (what exists in the world).
- **Workspace**: provider config (credentials) → model instance (what agents reference).
- **Platform models**: provider configs managed by AgentArea itself. Visible in every workspace, read-only for tenants, billed to the workspace balance. The one tagged `default` is what new agents start on; prefer it unless the user wants something specific.
- **Bring-your-own key**: the user creates a provider config with their own key (admin; prefer entering the key in the web app) and model instances on it. Usage is billed by their provider.

Choosing a model: cheap/fast for high-volume routine work, stronger models for reasoning-heavy or long agentic tasks. If unsure, start with the default and adjust after looking at results.
