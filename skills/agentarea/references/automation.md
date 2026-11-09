# Automation: triggers and bundles

## Cron triggers
`triggers_create_cron(name, agent_id, cron_expression, task_parameters={"text": "<what the agent should do each time>"}, timezone="UTC"|"Europe/Berlin"|…, enabled=false)`

- `task_parameters.text` is required: it is the instruction each run receives. Write it as a complete task, not a fragment.
- Set the timezone the user thinks in; the default is UTC.
- Every firing is a paid run. Triggers have no budget of their own — make sure the agent or workspace has a sensible per-run budget (`policies_preview_effective_policy`) before enabling.
- Recommended: create with `enabled=false`, run the same task once by hand (`runs_start`) and show the user the result, then `triggers_enable`.
- After `failure_threshold` consecutive failures (default 5) the trigger disables itself and stays off until re-enabled. `triggers_get_history` shows why.

## Webhook triggers
`triggers_create_webhook(name, agent_id, task_parameters={"text": …}, webhook_type="generic", allowed_methods=["POST"], event_types?, enabled=false)`

- The URL to register with the sender is `<API>/webhooks/<webhook_id>`. Webhook ids are unguessable, but signature verification is opt-in — set a signing secret (web app / REST `webhook_config.signing_secret`) for anything that matters.
- The incoming payload is available to the run alongside `text`.
- Send a test delivery before relying on it.

## Conditions
Triggers can carry conditions so only some events start a run. Model-evaluated conditions run an LLM call for **every** incoming event, outside the run budget — fine for low volume, expensive for chatty sources. Prefer simple field conditions when possible.

## Bundles and the catalog
A bundle installs a ready-made set (agents, MCP servers, skills, automations) into the workspace. Install via the web app (`https://app.agentarea.ai/bundles/import?src=<url>`) or REST (analyze, then install). There is no MCP tool for it.

- Analyze/preview first and tell the user what will be created.
- Installation is not transactional and has no uninstall — partial installs must be cleaned up by hand.
- Automations and channels from a bundle install **disabled**; enable them deliberately after checking.
