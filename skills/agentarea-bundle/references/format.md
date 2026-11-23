# Bundle folder format

The platform's parser is strict: an unknown key anywhere is an error that names the file and line, so write only the fields below. `agentarea deploy . --dry-run` is the authority; when this file and the plan disagree, believe the plan.

## agentarea.yaml

The only file with a fixed name and place. Everything else is found by glob.

```yaml
name: acme                     # the bundle's name in the workspace; required
schema_version: 1              # required; any other value is refused
display_name: Acme
description: Acme's agents, one folder per function
setup:                         # values asked at deploy, keyed by setup key
  model: {label: Model instance (name or id), required: true}
defaults:                      # only model, reasoning_effort, reasoning_max_tokens, limits
  model: ${setup.model}
  limits: {monthly_usd: 30, run_usd: 2}
agents:    {include: ./*/agents/*.md}
mcp:       {include: ./*/mcp/*.yaml}
openapi:   {include: ./*/openapi/*.yaml}
skills:    {include: ./*/skills/*/}
policies:  {include: ./*/policies/*.yaml}
schedules: {include: ./*/schedules/*.md}
tasks:     {include: ./*/tasks/*.md}
# also: channels, streams, projects; workspace: {policies: {include: ...}}
targets:                       # optional: named workspaces, each with its own setup values
  staging: {workspace: acme-staging}
  prod: {workspace: acme}
```

- `include` / `exclude` take a glob or a list: `*` and `?` stay inside one path segment, `**` crosses segments. `./*/mcp/*.yaml` matches `connections/mcp/x.yaml` and `sales/mcp/y.yaml` alike, which is what makes "one folder per function plus `connections/`" work with one line per section.
- A section with a glob that selects nothing only warns. Every file no include selects is listed as `ignored` (README, INVENTORY: expected). A file two sections select is an error.
- `defaults` refuses `mcp`, `skills`, `openapi`, `delegates` and `toolsets`: every grant of access is a line in that agent's own file, where a reviewer sees it.
- `setup` field keys: `label` (required), `type` (`string`, `secret`, `number`, `boolean`, `select`), `required`, `help`, `default`, `options`, `min`, `max`. Reference a value as `${setup.<key>}`; pass it with `--set key=value`.
- Limits: `monthly_<cur>` and `run_<cur>`, where `<cur>` is the workspace's billing currency in lower case (`usd`, `eur`, …). Another currency blocks the plan. Each becomes a cap policy per agent (`<agent>-monthly-cap`, `<agent>-run-cap`); an agent's own `limits` overrides a key, `null` drops it.

Kinds and file types: agents, schedules and tasks are Markdown with YAML front matter (body = prompt). MCP servers, OpenAPI connections, policies, channels, streams and projects are YAML. A skill is a directory with `SKILL.md`. An object's key is the `name` inside the file (`[a-zA-Z][a-zA-Z0-9_-]*`), not the file name; a mismatch only warns.

## Connections

**Link what the workspace already has.** This is the normal case for anything connected through OAuth or by hand:

```yaml
# connections/mcp/crm.yaml
name: crm
display_name: Sales CRM     # the connection's name in the workspace; defaults to name
existing: true
```

The deploy finds the workspace connection by that name, links it, and never creates, updates or deletes it. It takes nothing else (`catalog`, `json_spec`, `bindings`, `context_secret` are refused). The plan shows `already exists`; it blocks when the workspace has no connection with that name, or several. A connection this bundle created earlier cannot be turned into `existing`; give it a new key. The same works for OpenAPI connections (`connections/openapi/<name>.yaml` with `name` + `existing: true`).

**Let the bundle create one** when it is a plain catalog server or needs only a key:

```yaml
# connections/mcp/sheets.yaml
name: sheets
catalog: <catalog id of the server>
bindings:
  Authorization: "${secret.sheets-token}"   # a workspace secret, read each time the server starts
```

Exactly one of `catalog` or `json_spec`. A `bindings` key is a header for a remote server, an environment variable otherwise; a value is `${secret.<name>}` (the whole value) or something containing `${setup.<key>}`. Command servers run only with `npx`, `uvx`, `uv`, `python`, `python3`, `node`, `bunx`, `deno`; anything else is `unsupported` and its agents deploy without it. A created server cannot switch between `catalog` and `json_spec` or change transport on redeploy: give it a new key.

OpenAPI connection created by the bundle: `name`, `base_url` (required), `spec_url` or `spec`, `headers` / `query` / `variables` (credentials only as `${secret.…}` or `${setup.…}`), `description`. A `${secret.…}` value is copied at deploy time: after rotating the secret, redeploy.

## Skills

```
sales/skills/lead-scoring/SKILL.md      # front matter: name (the key), optional renamed_from
sales/skills/lead-scoring/references/…  # every text file in the directory ships with the skill
```

A skill directory inside another skill directory is an error. Selected with `skills: {include: ./*/skills/*/}`.

## Policies

```yaml
# sales/policies/crm-read-only-pipeline.yaml
name: crm-read-only-pipeline
subject: [pipeline]                 # an agent key, a list of keys, or "*" (every agent of the bundle)
target: "tool:mcp:crm:update_*"
effect: deny                        # deny | approval | cap | safety
message: The pipeline agent only reads the CRM
```

- A bundle policy only **tightens**, and only for the bundle's agents. `effect: allow` and `subject: workspace` are refused here. Rules for every agent in the workspace go under `workspace: {policies: …}`, have no `subject`, may `allow`, and deploy only for a workspace admin.
- A subject list of several (or `"*"`) becomes one policy per agent, keyed `<name>-<agent>`.
- `approvers: [person@example.com, "user:<id>"]` on an `approval` policy names who approves; each must be a member of the target workspace or the plan blocks. Without it, anyone who may act on the run approves.
- Targets for connection tools: `tool:mcp:<server name in the workspace>:<tool glob>` (fnmatch globs: `create_*`, `*`). These names can deny or require approval. Only a workspace policy with the instance **id** can allow. OpenAPI operations and delegates have their own forms (`tool:openapi:…`, `tool:agent:<id>`, `tool:a2a:<address>`); the `agentarea` skill's `references/governance.md` covers effects and enforcement.
- The plan prints each agent's approvals in its row. Read it to confirm the rule landed on the agent you meant.

## Schedules and saved tasks

```markdown
---
name: pipeline-monday
agent: pipeline
cron: "0 9 * * 1"
timezone: Europe/Berlin
enabled: false
---
Monday pipeline review: deals with no movement for 7+ days, one line each, and who should act.
```

- Exactly one of `agent` + a body (the prompt), or `task: <saved task key>` with an empty body (and optional `parameters`).
- `cron` or `on: {stream: <stream key or workspace stream name>, filter: {…}}` to run on stream events. A schedule cannot switch between `cron` and `on`, or move to another stream, on redeploy: give it a new key.
- Leaving `enabled` out also installs it disabled. Write `enabled: false` anyway so a reader sees the decision.
- A saved task (`tasks/*.md`): `name`, `agent`, optional `parameters`, body = prompt. Deploy saves it, never runs it. Good for a report you also want to run by hand.

## Streams, channels, projects

- **Streams** (`streams/*.yaml`): `name`, `display_name` (cannot change on redeploy), `sources` (each with a `type` the workspace offers, `kind` webhook/poll, `config`, `credentials` as secret/setup references), `processors` (`code`, `outputs`, `filter`), `forwards`. If the workspace already has a stream with that `display_name`, it is reused. Often simpler: point `on.stream` at a stream that already exists in the workspace, by its name.
- **Channels** (`channels/*.yaml`): `name`, `type: telegram`, `agent`, `bindings` (bot token as secret/setup reference), `enabled`. Install disabled unless set.
- **Projects** (`projects/*.yaml`): group the bundle's `agents`, `mcp`, `skills` by key, with `description` and `instructions`.

## Renames

An object is its key. Changing `name` alone creates a new object and leaves the old one `orphaned` (still running). To rename, set `renamed_from: <old key>` in the same file. Every reference (delegates, a schedule's `agent`, a policy's `subject`) follows. Remove `renamed_from` after the rename is deployed. Every kind takes it.

## Which install a deploy updates

After a deploy the CLI writes `.agentarea/deployments.json` (API URL + workspace → install id; no secrets). The next deploy updates that install, even if `name` changed. Commit it so teammates and CI hit the same install. Without it, `--into <bundle name or id>` picks the install; a deploy never silently writes into an existing bundle of the same name. A copied folder that keeps `.agentarea/` updates the original bundle, so read the plan's first line.

## What a redeploy does

- Objects the bundle created are updated in place when their file (or a `--set` value they use) changed, and left alone otherwise.
- An agent's tools and skills that the bundle declares (or attached last time) are replaced by the file's list; tools added to the agent in the workspace are kept on current platforms.
- **Deleting a file deletes nothing.** The object shows `orphaned` and keeps running. Archive or disable it by hand.
- Nothing is matched by name: a hand-made agent called the same is not this bundle's, and the deploy creates its own next to it.
- A deploy that fails partway removes what it created; running it again finishes the job. If someone deployed in between, the install refuses ("run deploy again to see the new plan").
- Created MCP servers re-discover their tools in the background after each deploy; the server's page shows the result.

## Organization folder (several workspaces)

A root `agentarea.yaml` with `teams:` (instead of sections) deploys several bundle folders, each into its own workspace, with one `agentarea deploy <org> --dry-run` / `--only-team <team>`. Shared files sit under `shared:` and a team includes them by path. `links:` between teams' agents are printed as `not applied yet`: cross-workspace delegation is not deployed by the folder, so use A2A (`teams-and-a2a.md`).
