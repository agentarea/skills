# AgentArea skills

Teach your AI assistant to work with [AgentArea](https://agentarea.ai): learn your organization, create and run agents, handle approvals, connect MCP servers and APIs, schedule work, and stay inside your policies and budgets.

## Claude Code

```
/plugin marketplace add agentarea/skills
/plugin install agentarea@agentarea
```

Then run `/mcp`, choose **agentarea**, and sign in in your browser. That's it — ask things like *"what agents do we have and what are they connected to?"* or *"run the support triage agent on today's tickets and wait for it to finish"*.

## Claude (web / desktop)

1. Settings → Connectors → **Add custom connector** → `https://api.agentarea.ai/mcp` → Connect.
2. Download [`agentarea.skill`](https://github.com/agentarea/skills/releases/latest) and add it in Settings → Capabilities → Skills.

## Codex, Cursor and other agents

```
npx skills add agentarea/skills
```

and connect the MCP server with the AgentArea CLI:

```
npm install -g @agentarea/cli
agentarea login --api-url=https://api.agentarea.ai
agentarea connect codex
```

## What's inside

- [`skills/agentarea`](skills/agentarea/SKILL.md) — how AgentArea fits together, how to find your way around a workspace, core workflows, and which actions need your confirmation (anything destructive, privileged, or that spends money). Details live in `references/`.
- [`skills/agentarea-builder`](skills/agentarea-builder/SKILL.md) — turns a need ("an agent that monitors tenders", "a small agency run by agents") into a concrete setup: finds what already exists in your workspace and the AgentArea catalog (bundles, preset agents, MCP servers, skills, built-in toolsets, event sources), proposes agents with each tool's source and the gaps named, and builds it once you agree. `scripts/catalog_search.py` searches the public catalog.

## License

Apache-2.0
