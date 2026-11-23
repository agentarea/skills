# Teams in a bundle, and agents in other workspaces

## Inside one bundle: `delegates`

A coordinator lists its specialists under `delegates: [key, …]`; each becomes a tool `delegate_to_<key>` (non-word characters become `_`; the run's events show the exact name). The specialist runs as its own task with its own tools and policies, and its final answer comes back to the coordinator.

- Split by what differs (tools, cadence, permissions, model), not by org chart. The `agentarea-builder` skill's `references/company.md` has the reasoning.
- A delegate must be an agent of the same bundle, and delegation may not form a cycle. Both block the plan.
- Write the specialist's `description` for the coordinator: it is what the coordinator reads when choosing whom to call.
- In the coordinator's instruction, say what to ask each specialist and what the specialist must not do in that call ("ask `intake`, and say it must not reply to anyone").
- Reports can also flow without delegation: specialists write their weekly report as their final answer, and the coordinator reads the last runs with the `agentarea/runs` toolset. That is cheaper than re-running each specialist and keeps the specialists' schedules independent.

## Another workspace or instance: A2A

A bundle can't name an agent outside itself. An organization folder's `links:` are not applied either. To let an agent ask an agent in another workspace (another business, another region, someone else's workspace) use an **A2A delegate**:

1. **In the target workspace**, issue an API key bound to the target agent (agent → Settings → A2A access → Issue key, or `POST /v1/workspaces/<ws>/api-keys/` with `agent_id`). The key reaches that one agent over A2A and nothing else. It acts as the member who issued it, so delegated tasks there are started by them. Copy the agent's **A2A address** from the same place.
2. **In the calling workspace**, store the key as a secret (web app → Secrets). The value never goes into the folder, a prompt or a chat.
3. **On the calling agent**, add a tool entry. Adding or changing one that sends a secret needs a workspace admin:
   ```json
   {"type": "agent", "name": "acme-lead",
    "settings": {"a2a_url": "<the target agent's A2A address>",
                 "auth_secret_name": "a2a-acme-lead",
                 "description_override": "Lead agent of Acme: weekly reports, open tickets, the pipeline. Ask it facts; it changes nothing."}}
   ```
   The model sees `delegate_to_acme_lead`. Via the API this is a `PATCH` of the agent's `tools`, which **replaces the whole list**, so read the current list first and send it back with the new entry.
4. **Test** with one task that needs the delegate, and check that a task for the target agent appears in the target workspace.

Worth telling the user: on current platforms the calling run waits for the remote task (for hours if needed), and several delegates called in one turn work at the same time, so "ask each CEO in one go" is fast. Older deployments gave up after about two minutes and the answer never came back. Either way, each call is a paid run in the other workspace, so ask remote agents short factual questions, not long jobs. On the target side, make the agent safe to be asked: a read-only policy on its write tools, and an instruction mode like "Question over A2A: answer from your sources in 3–6 lines; change and start nothing."

### Script the linking, and re-run it after deploys

These delegates are not in the bundle, so they live only in the workspace. A short, idempotent script keeps them reproducible. Keep it in the bundle repo, e.g. `scripts/link-<something>`. For each remote agent it:

1. finds the remote agent by name in its workspace (on its API);
2. if the calling workspace has no secret for it yet, issues an agent-bound key there and stores it as a secret in the calling workspace (otherwise it reuses the secret);
3. reads the calling agent's current `tools`, drops its own earlier A2A entries, appends the fresh ones, and writes the full list back;
4. prints the resulting tool list.

Run it once after the first deploy, and again after any redeploy or hand edit of that agent. Current platforms keep tools added outside the bundle on redeploy, but older ones replaced the whole list. Check the agent's tools after deploying either way. The script needs credentials for both workspaces; it must never print a key.
