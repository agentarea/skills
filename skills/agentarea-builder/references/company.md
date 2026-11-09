# Teams and agent-run companies

When the user wants "a support department", "an agency run by agents" or "a company", design it the way you'd staff a small team: few roles, clear handoffs, a human where it matters.

## Start from an example

Search bundles first (`catalog_search.py bundles <domain words>`). Several are whole teams — e.g. `design-bureau`: intake in Telegram → estimator → procurement → dispatch that sends mail only after the chief engineer approves, plus a Friday digest. Reuse its shape even when the domain differs.

## Split into roles by what differs

Make a separate agent when a piece of work differs in **inputs/tools**, **cadence** (on demand vs nightly), **permissions** (reads vs sends money or mail), or **model** (cheap triage vs strong reasoning). Don't split just to mirror an org chart — every extra agent is another instruction to maintain and another handoff that can lose context. Two to four agents is a good first version; propose the rest as "later".

## Wiring

- **Coordinator + specialists**: the coordinator has the specialists as tools (`{"type": "agent", "name": "<agent id>"}`) and decides whom to call. Good when requests vary.
- **Pipeline**: each agent's output feeds the next (via a shared file location or the coordinator). Good for fixed flows like intake → assess → act.
- **Scheduled roles**: digests, monitors and reports run on their own cron trigger, independent of the rest.

Agents call each other directly — no extra protocol needed. Create specialists first so the coordinator can reference their ids.

## Humans in the loop

Put an approval at every irreversible or outward-facing step: sending mail to clients, paying, submitting, publishing, deleting. Approvals are policy rules (the `agentarea` skill's `references/governance.md`), not a sentence in the instruction — an instruction can be ignored, a policy can't. Name who approves.

## Structure and limits

- One **project** for the team groups its agents, connectors and skills and is where per-person access is granted.
- Set a monthly and per-run **budget** for scheduled roles before enabling them.
- Give each agent only the tools its role needs (`allowed_tools` on MCP entries) — narrow tools are both safer and easier for the model to use well.

## Proposal shape for a team

One line per role (what it does, its tools with sources, its trigger), then the handoffs as a short arrow chain, then approvals and who gives them, then what the user must provide. Build in the order: connectors → skills → specialists → coordinator → triggers (disabled) → policies → project.
