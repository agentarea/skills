# Runs, events, input and approvals

## Lifecycle
| Status | Meaning | What you do |
|---|---|---|
| `submitted`, `preparing`, `pending`, `running` | In progress | Keep following events |
| `waiting_for_input` | Agent asked a question (expires after ~30 min) | Ask the user, answer with `runs_send_input` |
| `waiting_for_approval` | A tool call needs a human decision | Show it to the user, act only on their decision |
| `waiting_for_continuation` | Hit an iteration or budget limit (waits ~24 h) | Explain the limit and cost, continue only if they agree |
| `completed` | Done | Report the result |
| `failed`, `blocked` | Error or blocked by policy | Read events, explain why |
| `cancelled` | Stopped | — |

A cancelled run may still show `running` in lists for a while; trust events.

## Following a run
1. `runs_start(agent_id, description, parameters?)` → note the run id.
2. Poll `runs_get` and `runs_get_events` at a sensible interval (a few seconds early on, longer for long tasks). The event history is complete, so starting to read late loses nothing.
3. Terminal event types are `task.completed`, `task.failed`, `task.cancelled` (a blocked run emits `task.failed`). Don't stop on intermediate events.
4. Summarize: outcome, key actions taken, artifacts produced, cost if visible.

Useful event types: `llm.call.*`, `tool.call` / `tool.result`, `input.request` / `input.response`, `approval.request` / `approval.response`, `artifact.*`, `task.awaiting_continuation`, `task.*`.

`runs_list` only shows runs the current user started. For "what is happening across the workspace", use `inbox_list`.

## Input requests
The agent needs information. Ask the user the question verbatim (with any options), then `runs_send_input(run_id, input_request_id, answers)`. If the answer is a credential, don't send it as input — create a secret (or have the user add it in the web app) and tell the agent its name.

## Approvals (escalations)
A policy rule with effect `approval` paused a tool call. Get the details (`runs_list_pending_escalations` if available, otherwise the `approval.request` event), and present: which agent, which tool, with which arguments, and what it would do. Then wait. Call `runs_resolve_escalation(run_id, escalation_id, approved, comment)` only with the user's explicit decision — the decision is recorded under their identity.

Notes:
- Approvals have no timeout and send no notification; a run can sit there indefinitely. `inbox_list(status="waiting_for_approval")` shows them all.
- An approval rule with no approvers listed lets any member approve.

## Continuation
`waiting_for_continuation` means a limit was reached. Match the grant to the cause: more iterations for an iteration limit, more budget for a budget limit. `runs_continue_run` spends money and is privileged — confirm first.

## Follow-ups and steering
- After completion a run accepts follow-up messages for about 30 minutes (`runs_send_command(command="queue_message", message=…)`), keeping its context.
- `change_model` switches the model mid-run; `update_budget` raises the run budget (confirm — it spends).
- `runs_pause` / `runs_resume` for temporary holds; `runs_cancel` is destructive.
- Only the run's starter or a workspace admin can control a run.

## Scheduling a single run
`scheduled_at` on `runs_start` (ISO-8601 with timezone offset, in the future) runs once. For anything recurring, use a cron trigger.
