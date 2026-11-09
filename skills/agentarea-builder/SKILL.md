---
name: agentarea-builder
description: Turn a need ("I want an agent that monitors tenders", "set up a support team", "build me an agent company for our agency") into a concrete AgentArea setup — which agents, which tools, skills and schedules — by first finding what already exists in the workspace and the AgentArea catalog (bundles, preset agents, MCP servers, skills, built-in toolsets) and proposing that, then building it once the user agrees. Use this whenever someone wants a new agent, a team of agents, or a whole agent-run department or company on AgentArea, asks "what agent could do X", "which tools would an agent need for Y", or wants to automate a job with agents — even if they never say "AgentArea" or "catalog".
---

# AgentArea builder

Someone describes a job; you hand back a working setup on AgentArea. The value you add is **assembling, not inventing**: AgentArea already has thousands of MCP servers, skills, ready-made bundles and preset agents, and the user's workspace may already have half of what's needed connected. A proposal that says "take this preset, this connector you already have, and this catalog skill" is worth far more than a hand-written agent with tools that don't exist.

For how to operate the platform — exact tool arguments, MCP spec vs instance, verification, triggers, policies — use the `agentarea` skill (its `references/` folder). This skill decides *what* to build; that one knows *how* each call works.

## 1. Understand the job

Get just enough to choose the pieces. Ask at most 2–3 questions, and only ones whose answer changes what you build:

- **Where does the work come from?** A website or registry, an inbox, a chat, a CRM, files — this decides the connectors.
- **What is the output and where does it go?** A message in Telegram/Slack/mail, a document, an update in another system — this decides delivery.
- **When does it run?** On a schedule, on an event, when someone asks — this decides triggers.

For anything else (keywords, thresholds, tone), pick a sensible default, say what you assumed, and move on — the user can correct a concrete proposal far more easily than answer an abstract questionnaire. If the request is already specific, skip straight to discovery.

## 2. Find what can be reused

Look before proposing. Go from closest to farthest, because closer pieces are cheaper (already paid for, already authorized, already verified):

1. **The workspace** (needs the AgentArea MCP connection): `network_get_topology` or `agents_list` + `mcp_servers_list` (note verification status) + `skills_list` + `openapi_connections_list`. An existing agent that does 80% of the job may just need one more tool; a verified Telegram or Gmail instance means delivery is solved.
2. **Ready-made examples in the catalog** — bundles and preset agents. A bundle is a whole working setup (agents + connectors + skills + schedules); even when none fits exactly, the closest one shows the right *shape* and gives you an instruction to adapt.
3. **Capabilities in the catalog** — MCP servers and skills for each piece of the job.
4. **Built-in toolsets** — always available, no setup:

| Toolset | What it gives the agent |
|---|---|
| `agentarea/web` | Web search and reading pages — the fallback for any public website without an API |
| `agentarea/shell` | Bash in an isolated sandbox (Python, Node, curl); starts empty each run |
| `agentarea/files` | Text files in the run's working directory |
| `agentarea/context` | Read-only organization library (shared reference files) |
| `agentarea/media` | Image and video generation |

Plus `{"type": "agent"}` — another agent as a tool, the building block for teams (see `references/company.md`).

5. **Event sources** — how work *arrives*, not what the agent can call. `streams_list_source_types` lists them: RSS/Atom feeds, an IMAP mailbox, a Telegram bot, webhooks, and more. A stream source plus a stream trigger (optionally batched, e.g. once a day) often beats an agent that polls a website on a cron: many registries and sites offer RSS for a saved search, a mailbox can be watched instead of scraped, a form can post to a webhook. Check this before falling back to reading pages.

### Searching the catalog

Run the bundled script (Python 3, no dependencies; downloads the public catalog once and caches it):

```bash
python3 <this-skill>/scripts/catalog_search.py all tender procurement rfp bid --limit 5
python3 <this-skill>/scripts/catalog_search.py mcp slack
python3 <this-skill>/scripts/catalog_search.py skills pdf extract table
```

Kinds: `bundles`, `agents`, `mcp`, `skills`, `all`. Search with several English synonyms plus the user's own words — catalog entries are mostly in English, and "tender" alone misses "procurement" and "RFP". Run a separate search per capability (source, processing, delivery) rather than one query for the whole job. `--market <code>` drops servers published only for other markets.

Then check how the workspace can install what you found: `mcp_servers_list_specs(search="<name>")` returns the catalog spec ready to instantiate. If the script's server isn't there, it can still be added (from the web app's Explore → Connections, or by creating a spec as the `agentarea` skill's `references/mcp.md` describes) — say which.

No shell available? Use `mcp_servers_list_specs(search=…)` and `skills_list`, and point the user to Explore in the web app for bundles.

### Judge what you found

A search hit is a candidate, not an answer. Read the description: is it for the right country/system? Vendor-hosted (needs an account or key with that vendor) or a package the platform runs? Does it need credentials the user may not have? Prefer, in order: already connected and verified → catalog item from a known vendor → community package → built-in web/shell fallback.

**Name gaps honestly.** If nothing covers a piece — say, there's no connector for the registry the user cares about — say so and offer real options, best first: an event source (RSS, mail, webhook) if the system offers one, an OpenAPI connection if it has an HTTP API, `agentarea/web` + `agentarea/shell` to read the public site, or building a connector. Never present a fallback as if it were a proper integration, and never invent a tool name.

**Reachable from where the agent runs?** Agents run on the platform, not on the user's machine. Some sites (government portals especially) block or time out for requests from cloud or foreign IP ranges, and the platform's egress may not reach them at all. When the plan depends on a site, say this is unverified and make "check the source answers from the platform" the first thing the test run proves — don't promise a daily digest from a source nobody has reached yet.

## 3. Propose

Show one proposal per agent, compact enough to read in a minute. Mark where each piece comes from — that's the point of the exercise:

```
**Tender scout** — based on the `release-radar` bundle pattern (watch → daily digest)

| Need | Piece | Source |
|---|---|---|
| Find new notices | <connector or fallback> | catalog / built-in / ⚠️ gap |
| Remember what was already sent | agentarea/files | built-in |
| Deliver | Telegram (instance "ops-bot") | ✅ already connected |
| Schedule | cron weekdays 09:00 in the user's timezone | trigger, created disabled |
| Guardrails | read-only; never submits anything | policy |

Model: platform default. Instruction (summary): …
Needs from you: <keys, OAuth sign-ins, accounts>
Cost: one run per firing on the workspace balance
Later: <the natural next agent, if the job grows>
```

Include the instruction you would give the agent (a short draft is fine — role, inputs, output format, what to do when stuck, what never to do). List everything the user must provide — keys, OAuth sign-ins, vendor accounts — so nothing surprises them during the build.

If the job is really several jobs with different inputs, cadences or permissions, propose a small team instead of one overloaded agent — read `references/company.md`.

Stop here and ask for a go-ahead. The proposal is the moment the user corrects course cheaply.

## 4. Build

Only after the user agrees, and in the workspace they confirmed (on an account-wide endpoint, ask which one). Follow the `agentarea` skill for each call; the order that avoids half-built setups:

1. Connectors: reuse existing instances; create new ones, and **verify** each — an unverified instance gives the agent no tools at all. OAuth and secrets go through the web app, not the chat.
2. Skills: import or create, so their ids exist.
3. Agents: create with the full `tools` list and instruction (for a team, specialists before the coordinator that references them).
4. Triggers: create **disabled**.
5. Policies and project grouping if the proposal had them.

Don't start runs or enable schedules as part of setup — every run costs money and acts on real systems. Finish with what was created (names and ids), what is still waiting on the user (sign-ins, keys, enabling the trigger), and offer a first test run.

If something fails midway, stop, say exactly what exists now and what doesn't, and ask before cleaning up or retrying.

## Without an AgentArea connection

You can still do steps 1–3 with the catalog script and produce the proposal. To build, the user needs the AgentArea MCP connected — the `agentarea` skill's `references/connect.md` walks through it.
