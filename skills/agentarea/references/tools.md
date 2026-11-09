# AgentArea MCP tools

Every tool has an effect class: **read**, **write**, **destructive** or **privileged** (changes someone's rights, limits or reach). Your client is not told which is which, so use this file. On the account-wide endpoint (`…/mcp`) every tool below except `workspaces_*` also takes a required `workspace` argument.

Tools marked *(newer)* may not exist on every server.

## workspaces (account-wide endpoint only)
- `workspaces_list(query?)` — workspaces the user can reach. Call first on `…/mcp`.
- `workspaces_create(name)` — write.

## agents
- `agents_list(limit, offset)`, `agents_get(agent_id)` — read.
- `agents_create(name, model_id, tools, description?, instruction?, agent_type?)` — write. `tools` is required (use `[]`). `model_id` is a model instance id. `agent_type` has no effect.
- `agents_update(agent_id, name?, description?, instruction?, model_id?)` — write. Cannot change tools or skills.
- `agents_delete(agent_id)` — destructive.

## runs
- `runs_start(agent_id, description, parameters?, project_id?, scheduled_at?, requires_human_approval?)` — write, spends money. `scheduled_at`: ISO-8601 with offset, in the future, fires once (use a cron trigger for repeats). `requires_human_approval` is currently not enforced.
- `runs_list(agent_id?, limit)` — read. Lists only runs **started by the caller**; `agent_id` is ignored.
- `runs_get(run_id)` — read: status, result.
- `runs_get_events(run_id, limit=50, offset, event_type?)` — read: the timeline (id, type, timestamp, message).
- `runs_list_pending_escalations(run_id)` *(newer)* — read: the exact tool + arguments awaiting approval.
- `runs_send_input(run_id, input_request_id, answers)` — write. Refuses secrets.
- `runs_resolve_escalation(run_id, escalation_id, approved, comment)` — **privileged**. Only on the user's explicit decision.
- `runs_continue_run(run_id, additional_iterations?, additional_budget_usd?, additional_tokens?, additional_tool_calls?)` — **privileged**, spends money. Grant what matches the limit that was hit.
- `runs_pause`, `runs_resume` — write.
- `runs_send_command(run_id, command, …)` — write. Commands: `queue_message` (message), `remove_message` (message_id), `change_model` (model_instance_id), `update_budget` (budget_usd — spends money).
- `runs_cancel(run_id)` — destructive.
Control tools work only for whoever started the run or a workspace admin.

## inbox
- `inbox_list(status?, agent_id?, page, page_size)` — read. Statuses: `waiting_for_approval`, `waiting_for_input`, `completed`, `failed`. The workspace-wide "what needs a human" view.

## projects
- `projects_list/get` — read. `projects_create(name, description?, instructions?, parent_project_id?)`, `projects_update` — write. `projects_delete` — destructive.
- `projects_add_/remove_agent`, `projects_add_/remove_skill`, `projects_add_/remove_mcp_instance` — write.

## models and providers
- `models_list_specs`, `models_list_instances`, `models_get(model_instance_id)` — read. The instance list may not show tags; platform models are the ones on AgentArea-managed provider configs.
- `models_create_instance(provider_config_id, model_spec_id, name, description?)` — write.
- `providers_list_specs`, `providers_list_configs` — read.
- `providers_create_config(provider_spec_id, name, api_key, endpoint_url?, …)`, `providers_update_config` — **privileged**, admin. The api key passes through the chat; prefer the web app.
- `providers_delete_config` — destructive, admin.

## mcp_servers
- Specs (how to run/reach a server): `mcp_servers_list_specs(is_public?, tag?, search?, limit≤100, offset)`, `mcp_servers_get_spec` — read. `mcp_servers_create_spec(...)`, `mcp_servers_update_spec` — write. `mcp_servers_delete_spec` — destructive.
- Instances (configured copies agents use): `mcp_servers_list`, `mcp_servers_get` — read. `mcp_servers_create(name, server_spec_id, json_spec_json, description?, auth_config_id?)`, `mcp_servers_update` — write. `mcp_servers_delete_instance` — destructive.
- `mcp_servers_verify(instance_id)` — provisions the server, waits, lists its tools. Check the instance's verification status afterwards; a successful call is not a successful verification.
- Several arguments are JSON-encoded strings (`*_json`).

## openapi_connections
- `openapi_connections_list/get` — read. `create(name, base_url, spec_url? | spec_content_json?, auth_config_id?, custom_headers_json?, url_variables_json?)`, `update`, `discover_tools` — write. `delete` — destructive.

## skills
- `skills_list`, `skills_get`, `skills_list_files`, `skills_get_file(skill_id, path, as_url?)` — read.
- `skills_create(files{path: content}, name?, description?)`, `skills_create_from_archive(zip_base64)`, `skills_import_from_github(github_url, name?, description?, skill_name?, import_all?)`, `skills_edit_metadata`, `skills_edit_content(skill_id, files)` — write. A repo with several SKILL.md files returns candidates: choose with `skill_name` or set `import_all`.
- `skills_delete` — destructive.

## triggers
- `triggers_list(agent_id?, active_only?, limit)`, `triggers_get`, `triggers_get_history` — read.
- `triggers_create_cron(name, agent_id, cron_expression, task_parameters, timezone="UTC", description?, conditions?, enabled?, failure_threshold=5)` — write, recurring spend. `task_parameters` must include `text` (the instruction for each run).
- `triggers_create_webhook(name, agent_id, task_parameters, webhook_type="generic", allowed_methods?, conditions?, event_types?, enabled?, failure_threshold?, webhook_id?)` — write. URL: `<API>/webhooks/<webhook_id>`.
- `triggers_enable`, `triggers_disable` — write. `triggers_delete` — destructive.

## secrets
- `secrets_list` — read, names only.
- `secrets_create(name, value, description?)` — **privileged**, admin. `secrets_delete(name)` — destructive, admin.

## workspace_files
- `workspace_files_list(prefix?, max_items?)`, `workspace_files_get_url(path, expires_in?)` — read.
- `workspace_files_upload_urls(files[{path, sha256, content_type?}])` *(newer)* — write, ≤100 per call. For whole folders the CLI's `agentarea files sync` is better.
- `workspace_files_delete` — destructive.

## members
- `members_list` — read.
- `members_invite(email?, expires_in_days?)`, `members_list_invitations`, `members_revoke_invitation` — **privileged**, admin. The invite token is shown once.
- `members_remove(user_id)` — destructive. Only the owner removes others; the owner and the last member cannot be removed.

## policies
- `policies_preview_effective_policy(agent_id?)`, `policies_get_run_policy(run_id)` — read, any member.
- `policies_list/get` — read, admin. `policies_create(subject_type, subject_id, target, effect, params?, enabled?, …)`, `policies_update` — **privileged**, admin. `policies_delete` — destructive, admin. Rules the engine cannot enforce are rejected on write.

## clients (registered harness endpoints)
- `clients_list/get` — read. `clients_create(name, description?, kind="harness")`, `clients_update` — write. `clients_delete` — destructive (endpoint stops working).
- `clients_add_mcp_instance(client_id, mcp_instance_id, namespace_prefix?, allowed_tools?)`, `clients_add_skill`, `clients_add_platform_toolset(client_id, toolset, disabled_methods?)` *(newer)* — **privileged** (widen an outside harness's reach). Matching `remove_*` — write.

## network, audit, export
- `network_get_topology()` — read, any member. Graph of agents, skills, MCP instances, triggers.
- `audit_list(action?, actor_id?, resource_type?, resource_id?, since?, until?, cursor?, limit?)` — read, admin.
- `workspace_config_export()` — read, admin. `{yaml: …}` importable bundle.

## Not available over MCP
Installing catalog bundles and managing API keys are web app / REST only.
