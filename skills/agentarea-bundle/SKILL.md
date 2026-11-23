---
name: agentarea-bundle
description: Author and ship a whole AgentArea workspace as a versioned bundle folder. The folder holds `agentarea.yaml` and one folder per business function, with agents as Markdown files, connections linked by name (`existing: true`), skills, policies, disabled schedules and saved tasks. You dry-run, deploy and redeploy it with the `agentarea` CLI. Use this whenever the user wants agents kept in git or reproducible, wants to "deploy a folder", edits an `agentarea.yaml` or an agent `.md` file, adds, renames or retires an agent in an existing bundle, moves a hand-built workspace into files, or connects agents across workspaces, even if they never say "bundle".
---

# AgentArea bundle folders

A bundle folder is a workspace written down: `agentarea.yaml` at the root, one folder per function (sales, support, chief, …), and in each the agents as Markdown files plus their skills, policies, schedules and saved tasks. `agentarea deploy` shows a plan, installs it into one workspace, and the next deploy updates the same install. The folder is the source of truth, kept in git and reviewed like code. Nobody fixes things in the web UI and hopes to remember.

Use a folder when the setup should be repeatable, reviewable, or redeployed to another workspace. For a one-off (one agent to try something, a quick fix), plain MCP calls from the `agentarea` skill are simpler. That skill also explains how each platform object works; this one covers the folder route. To decide *what* agents a business needs, start with `agentarea-builder`.

## The shape

```
acme/
├── agentarea.yaml            name, schema_version: 1, setup, defaults, include globs
├── README.md                 the human map: layout, who does what, how to deploy, open questions
├── INVENTORY.md              optional: agents × model × connections × schedules, one table
├── connections/
│   ├── mcp/crm.yaml          name + existing: true  (connected in the workspace already)
│   └── openapi/…
├── shared/skills/<skill>/    used by two or more functions
├── sales/
│   ├── agents/pipeline.md    front matter = config, body = instruction
│   ├── skills/<skill>/SKILL.md
│   ├── policies/*.yaml       next to the agent they limit
│   ├── schedules/*.md        enabled: false
│   └── tasks/*.md            saved prompts, run by hand or by a schedule
└── support/ …
```

With includes like `agents: {include: ./*/agents/*.md}` and `mcp: {include: ./*/mcp/*.yaml}`, one line per section picks up every function folder and `connections/`. Keys (`name` in each file) are unique across the whole bundle; moving a file between folders changes nothing. A complete small example sits in `references/example/` and parses cleanly: two functions, three agents, one existing connection, one approval policy, one disabled schedule. Field-by-field format: `references/format.md`.

## Workflow

**1. Discover before writing.** With the AgentArea MCP connected, in the workspace the user confirmed:
- `mcp_servers_list` and `openapi_connections_list`: exact names and verification status. Anything already connected (especially OAuth) goes in as `existing: true` under its exact workspace name.
- `models_list_instances`: the model names agents may use.
- `agents_list`: hand-made agents the bundle will replace. The deploy never adopts them by name; it creates its own, so plan to archive the old ones after the new ones work.
- `secrets_list` (names only), `streams_list`, `members_list` (approvers must be members), `policies_preview_effective_policy`.
For an existing bundle, read `agentarea.yaml`, the README and the files you will touch first.

**2. Write the folder.** Agents per `references/agents.md`. Every schedule and channel `enabled: false`. Secrets only as `${secret.<name>}` or `${setup.<key>}`, never values. Update the README / inventory in the same change.

**3. Dry run and read the plan:**
```bash
agentarea deploy . --workspace <slug> --dry-run      # writes nothing
```
Check, in order: the first line (does it **create** a bundle or **update** the one you expect?), the agents table (each agent's skills, MCP, OpenAPI, delegates, approvals), every object's status (`create`, `update`, `unchanged`, `already exists`, `orphaned`, `unsupported`, `ignored`), and the issues. A blocking issue stops the deploy; fix the file and run it again. Show the user the plan in plain words.

**4. Deploy on the user's yes:** `agentarea deploy . --workspace <slug>` (add `--set key=value` for setup values; `--yes` only when the user already approved this exact plan). The install carries out exactly the plan shown. Commit `.agentarea/deployments.json` with the folder so the next deploy updates the same install.

**5. Verify.** Every linked or created MCP instance has a **succeeded** verification and a non-empty tool list (`mcp_servers_get`). An unverified instance gives its agents no tools at all, silently. Then spot-check one agent's tools and its effective policy.

**6. First run only on the user's word.** Offer one test run of the most important agent, follow it to the end, show the result. Then the user decides which schedules to enable, one at a time, after checking the monthly cap.

**7. Every later change goes through the folder:** edit → dry run → deploy → commit. A change made in the UI is invisible to the folder and may be overwritten or orphaned by the next deploy. If someone did change something by hand, write it into the files first.

## Governance belongs in files

A sentence in a prompt is a request; a policy is enforced. For every write an agent should not make on its own, add a policy file next to it:

- **read-only**: `effect: deny` on the write tools, e.g. a chief / CEO-type agent that reads the CRM but must not change deals, or an engineering reporter that must never push to GitHub (`target: "tool:mcp:github:*_write"`, `create_*`, `merge_*`, …: one file per glob is fine);
- **approval**: `effect: approval` on anything customers or the public see (send, publish, reply), with `approvers:` when it must be a specific person;
- **money**: `limits` (monthly and per run) in `defaults` and tighter per agent. Set the monthly cap before any schedule is enabled, because every firing is a paid run.

Target connection tools as `tool:mcp:<server name in the workspace>:<glob>`. Copy tool names from the verified instance; a policy on a name the server doesn't have never fires. Then read the approvals column of the plan to confirm the rule landed on the agent you meant.

## Teams and other workspaces

Inside the bundle, a coordinator lists specialists under `delegates:`. Agents in **another workspace or instance** are reached over A2A instead: an agent-bound key issued there, stored as a secret here, and an `agent` tool with the A2A address. That link lives outside the folder, so script it and re-run the script after redeploys. Details and the script's steps: `references/teams-and-a2a.md`. An agent run by an external harness (`client:`) gets its tools from the client, not from its `mcp:` list: `references/agents.md`.

## Gotchas learned the hard way

- **Deploy never writes an `existing: true` connection.** Create it and finish its sign-in (OAuth, key) in the workspace first; the plan blocks if the name matches none or several. Platform-managed connections link the same way.
- **Unverified MCP instance = agent with no tools.** No error; the agent just can't do the job. Verify after every deploy that touches connections.
- **Deleting a file deletes nothing.** The object turns `orphaned` and keeps running (a schedule keeps firing if enabled). Disable or archive it by hand, and say so.
- **Renaming = `renamed_from`.** A changed `name` alone creates a second agent next to the old one.
- **External harness runners** need their own harness login kept fresh on the machine that runs them; while no runner is online, runs wait.
- **Messenger chats** (a Telegram bot): messages from one chat join one running task until it goes idle (about 30 minutes by default), then a new task starts. Design the agent for a conversation, not one message.
- **Group chats:** instruct agents to post at most a few lines; the detail goes in the run's final answer.
- **No secrets in the folder,** not even in a private repo. Bot tokens, API keys and A2A keys live as workspace secrets; files reference them by name.
- **Currency:** `limits` keys use the workspace's billing currency (`monthly_eur`, …); a wrong one blocks the plan.
- **A copied folder with `.agentarea/`** deploys into the original bundle. Read the plan's first line.

## Act carefully

- Dry runs and reads are free; ask before every real deploy, before enabling any schedule or channel, before the first run, and before issuing keys or creating secrets.
- Never enable schedules "to test". Run the agent once by hand instead.
- Several workspaces (`targets:`, `--target`)? Confirm which one before each deploy. Secrets and connections resolve in the target workspace and are never copied between them.
- When a deploy fails, read the issue: it names the file and line. A failed install cleans up what it created; running the same command again finishes the job.

## Reference files

- `references/format.md`: `agentarea.yaml`, include globs, connections (`existing`, catalog, bindings), skills, policies, schedules, tasks, streams, channels, renames, redeploy behaviour, organization folders.
- `references/agents.md`: every agent front matter field, `client:` runners, and how to write the instruction body.
- `references/teams-and-a2a.md`: delegates inside a bundle; A2A delegates across workspaces and the linking script.
- `references/example/`: the complete minimal example bundle.
