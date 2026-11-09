# Governance: members, policies, approvals, budgets, audit

## Members and roles
`members_list` shows who belongs to the workspace and their role. Admin-only actions: policy writes, secrets, provider configs, invitations, audit, config export. Only the owner can remove other members; the owner and the last member can't be removed. When a tool fails with an authorization error, tell the user which role is needed rather than retrying.

## Policies
A policy rule = **subject** (workspace, agent, or user) + **target** + **effect** (+ params).

| Effect | Use |
|---|---|
| `allow` / `deny` | Permit or forbid tools: target `tool:<glob>` or `*` |
| `approval` | Pause matching tool calls until a human approves (`params.approvers: ["user:<id>"]`) |
| `cap` | Limits on `spend`, `service`, `tokens` |
| `safety`, `egress` | Content safety and network egress controls |

- Layers merge workspace → agent → user → task and can only **tighten**; a lower layer cannot grant what a higher one denies.
- Rules the engine cannot enforce are rejected when written.
- Before and after writing a rule, check `policies_preview_effective_policy(agent_id)` to confirm the effect — this is how you show the user what will actually apply.
- For a live run, `policies_get_run_policy(run_id)` shows the resolved policy.

### Human in the loop
To require approval for risky actions, create an `approval` rule on the specific tools (e.g. `tool:github__create_pull_request`, `tool:*send*`) for the agent, with explicit approvers. Don't rely on `requires_human_approval` when starting a run — it is not enforced. An approval rule with no approvers lets anyone approve; group approvers currently match nobody. Approvals don't time out or notify — point people to the inbox.

## Budgets
- `monthly_spend_cap_usd` — checked when a run is created; exceeding it returns HTTP 402 `budget_cap_exceeded`.
- `run_budget_usd`, `max_tokens` — per run; hitting them pauses the run in `waiting_for_continuation`.
- Amounts are in the workspace's **billing currency** even though the field names say `_usd`.
- New workspaces start with defaults (roughly 500 per month, 50 per run, 20M tokens) — check the effective policy rather than assuming.
- Separately, the workspace balance pays for platform-provided models and compute; `no_credits` errors mean the balance is empty — tell the user to top up, don't work around it.

## Audit and export
- `audit_list(...)` (admin) — who did what and when; filter by actor, resource, action, time.
- `workspace_config_export()` (admin) — YAML snapshot of agents, MCP servers, skills and triggers; good for review, backup, or reproducing a setup elsewhere.
