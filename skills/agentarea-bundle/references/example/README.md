# Corner Bikes on AgentArea

An invented example: the bundle for a small bicycle repair shop's workspace. Copy the shape, not the shop.

## Layout

```
agentarea.yaml        name, setup, defaults, which files belong to the bundle
connections/mcp/      helpdesk.yaml: existing: true, already connected in the workspace; the bundle never changes it
support/              agents/intake.md, agents/parts.md, policies/customer-replies-approval.yaml
chief/                agents/lead.md, schedules/friday-report.md
```

- A skill one function uses lives in its folder; when a second function needs it, it moves to `shared/`.
- A policy lives next to the agent it limits.
- `name` inside a file is the object's key and is unique in the whole bundle. Moving a file between folders changes nothing.

## Who does what

| Folder | Agent | Does | Tools | When |
|---|---|---|---|---|
| `support/` | Intake (`intake`) | triages tickets, drafts replies; replies only after approval | helpdesk, asks `parts` | on request |
| `support/` | Parts (`parts`) | finds parts and prices on suppliers' sites | `agentarea/web` | asked by `intake` |
| `chief/` | Lead (`lead`) | Friday report for the owner, answers questions | `agentarea/runs`, asks `intake` | Fri 16:00, **disabled** |

Every agent: the model given at deploy, at most 20 a month and 1 per run (`defaults.limits`; write the amounts in the workspace's billing currency, `usd` here).

The helpdesk tool names in `intake.md` and in the policy (`list_tickets`, `set_priority`, `add_note`, `send_reply`) stand in for whatever the real helpdesk server lists once its connection is verified. Copy the real ones before deploying.

## Deploy

```bash
agentarea deploy . --workspace corner-bikes --set model=<model instance> --dry-run
agentarea deploy . --workspace corner-bikes --set model=<model instance>
```

The CLI records the install in `.agentarea/deployments.json` (commit it); after that `agentarea deploy .` is enough. The schedule installs disabled: turn it on yourself after a test run.

## Open questions

- Who approves customer replies: anyone who may act on the run, or only the owner (`approvers:` in the policy)?
