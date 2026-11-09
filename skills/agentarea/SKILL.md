---
name: agentarea
description: Operate an AgentArea workspace through its MCP tools — learn the organization (members, projects, agents, models, MCP servers, skills, triggers, inbox), create and configure agents, start runs and follow them to the end, handle approvals and input requests, connect MCP servers and APIs, schedule agents with triggers, and work within policies and budgets. Use this whenever the user mentions AgentArea, an AgentArea workspace, agents/runs/tasks/inbox/escalations/triggers/policies in that context, or when tools named like `agents_*`, `runs_*`, `inbox_list`, `network_get_topology`, `policies_*`, `mcp_servers_*` or `workspaces_list` are available — even if the user does not say "AgentArea" explicitly.
---

# AgentArea

AgentArea is a platform where a company runs AI agents as part of its organization: each agent has instructions, a model, tools (MCP servers, APIs, code), skills, and runs under the workspace's policies, budgets and approvals. You reach it through the AgentArea MCP server. This skill tells you how the pieces fit, how to find your way around a workspace you have never seen, and which actions need the user's say-so.

If no AgentArea tools are available, the user has not connected yet — read `references/connect.md` and walk them through it.

## First: which endpoint am I on?

The MCP server has two shapes, and the tool signatures differ:

- **Workspace-pinned** (`…/mcp/w/<workspace>`): tools take no `workspace` argument. Everything happens in that one workspace.
- **Account-wide** (`…/mcp`): every workspace-scoped tool requires a `workspace` argument (slug or id), and `workspaces_list` / `workspaces_create` exist. Call `workspaces_list` first, and if the user belongs to more than one workspace, confirm which one before changing anything. Acting in the wrong workspace is the easiest serious mistake to make here.

A tool missing from your list may simply be filtered (`?toolsets=…` on the URL) or newer than the server you are connected to — say so rather than inventing a workaround.

## Learn the organization before acting

When the user asks something about "our agents", "what's running", or wants a change in an unfamiliar workspace, build a picture first — it is cheap and prevents duplicates and wrong assumptions:

1. `members_list` — who is here, and whether the user is an admin (admin-only tools fail otherwise).
2. `network_get_topology` — one call that returns the graph of agents, skills, MCP instances and triggers and how they connect. Best single overview.
3. `projects_list`, then `agents_list` / `agents_get` for the agents that matter (instruction, model, tools).
4. `models_list_instances` (what models agents can use), `mcp_servers_list` (check each instance's verification status), `skills_list`, `triggers_list`.
5. `inbox_list` — what is waiting on a human right now (approvals, input requests, failures).
6. `policies_preview_effective_policy(agent_id)` — the limits, budgets and approval rules that will actually apply to an agent.
7. Admins only: `workspace_config_export` (full YAML snapshot of agents, MCPs, skills, triggers) and `audit_list` (who changed what).

Summarize what you found in plain terms before proposing changes. Don't dump raw JSON on the user.

## The model, in one screen

- **Workspace** is the isolation boundary. **Projects** group agents, skills and MCP instances (and anchor permission grants) but do not isolate anything.
- **Agent** is a definition, not a process: `instruction`, `model_id`, `tools`, `skills`. `model_id` is a **model instance id** from `models_list_instances`, not a model name. Platform-provided models (managed by AgentArea) are visible in every workspace; the one tagged `default` is the sensible choice when the user has no preference.
- **Tools on an agent** are a list of typed entries — MCP instance, OpenAPI connection, built-in code tool, or another agent. Having a tool configured does not mean it may be used: policy decides. Details: `references/agents-and-models.md`.
- **Run (task)** is one execution of an agent. It moves through `submitted → pending/running → completed | failed | blocked | cancelled`, and can pause in `waiting_for_input`, `waiting_for_approval`, or `waiting_for_continuation` (hit an iteration or budget limit). Details: `references/runs-and-approvals.md`.
- **MCP server spec vs instance**: a spec describes how to run/reach a server; an instance is a configured, credentialed copy in this workspace that agents actually use. Details: `references/mcp.md`.
- **Policies** (allow / deny / cap / approval …) layer workspace → agent → user → task and can only tighten. **Budgets** cap spend per month and per run. Details: `references/governance.md`.
- **Triggers** start an agent on a cron schedule or a webhook. Details: `references/automation.md`.

## Core workflows

**Run an agent and see it through.** `runs_start(agent_id, description)` → poll `runs_get` / `runs_get_events` until a terminal state. Stop on `completed`, `failed`, `blocked` or `cancelled` — not earlier. If it pauses:
- `waiting_for_input` → ask the user the question and answer with `runs_send_input`.
- `waiting_for_approval` → show the user exactly what the agent wants to do (tool + arguments, from `runs_list_pending_escalations` if available) and let *them* decide; then `runs_resolve_escalation`.
- `waiting_for_continuation` → tell the user which limit was hit and what continuing costs; only call `runs_continue_run` if they agree.
Report the outcome in one or two sentences plus anything the agent produced. Note: `runs_list` returns only runs started by the current user, so it is not a view of everything happening in the workspace — use `inbox_list` for that.

**Create an agent.** Pick a model instance (prefer the platform `default` unless told otherwise) → `agents_create(name, model_id, tools=[...], instruction=...)`. `tools` is required — pass `[]` if none yet. `agents_update` cannot change tools or skills; see `references/agents-and-models.md` for how. Write the instruction like a job description: role, goal, what good output looks like, what to do when stuck.

**Set up an MCP server / give an agent a new capability.** Read `references/mcp.md` first — the arguments are JSON strings with exact shapes, OAuth needs the user in a browser, and an instance that hasn't verified successfully gives agents no tools at all. Order: reuse a verified instance → catalog spec (`mcp_servers_list_specs(search=…)`) → build a spec → create instance → verify and check `succeeded` → attach. Non-MCP HTTP APIs: OpenAPI connections (`references/integrations.md`).

**Automate.** Create the trigger disabled, fire it once to check the result, then enable it (`references/automation.md`).

## Act carefully — this touches a real company

These rules exist because the actions are real: they spend money, change who can do what, or delete work other people rely on.

- **Ask before anything destructive**: any `*_delete`, `mcp_servers_delete_instance` / `delete_spec`, `runs_cancel`, `workspace_files_delete`, `members_remove`, `secrets_delete`, deleting a client (its endpoint stops working for whoever uses it). Name the exact object and its consequences, then wait for a yes.
- **Ask before privileged actions** — anything that changes rights, limits or reach: `runs_resolve_escalation`, `runs_continue_run`, policy writes, `members_invite`, provider configs, `secrets_create`, `clients_add_*`.
- **Never approve an escalation on the user's behalf.** The approval is recorded as theirs; it is a human control, not a step to automate. Present it, let them decide.
- **Money.** Every run, every trigger firing, continuing with more budget, and model-evaluated trigger conditions cost money. Before starting something long or repeated, check `policies_preview_effective_policy` and say roughly what will happen. A `budget_cap_exceeded` (HTTP 402) or `no_credits` error means stop and tell the user — don't retry or raise limits on your own.
- **Secrets.** Never print secret values. Values typed into a conversation (API keys for providers, `secrets_create`, MCP headers) pass through the chat — prefer that the user enters them in the AgentArea web app, or reference an existing secret by id. `runs_send_input` refuses secrets on purpose; create a secret instead.
- **Approvals at run start.** The `requires_human_approval` flag on `runs_start` does not enforce anything today. If the user wants a human in the loop, write an approval policy rule (`references/governance.md`).
- **Bulk or irreversible setup** (catalog bundles) has no uninstall — preview what it will create first.

When something fails, read the error: authorization errors usually mean the user lacks a role (say which), "not found" on a pinned endpoint can also mean "not a member", and a tool error on a run is usually in `runs_get_events`.

## Reference files

Read only the one you need:

- `references/connect.md` — connecting Claude Code, Claude desktop/web, Codex and other harnesses; endpoints, OAuth, API keys, regions.
- `references/tools.md` — every toolset with key arguments and gotchas.
- `references/agents-and-models.md` — agent fields, tool entry shapes, skills on agents, model layers and the `default` model.
- `references/runs-and-approvals.md` — run statuses, events, input, approvals, continuation, follow-ups, commands.
- `references/mcp.md` — setting up MCP servers end to end: catalog, exact spec/instance shapes (remote OAuth, API key, npx/uvx, docker), credentials, verification and its failures, attaching to agents.
- `references/integrations.md` — OpenAPI connections, skills, secrets, workspace files, clients.
- `references/automation.md` — cron and webhook triggers, conditions, failure thresholds, bundles and the catalog.
- `references/governance.md` — members and roles, policies, approvals, budgets, audit.
