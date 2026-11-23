---
tags: [agentarea-bundle]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Our bundle is the example in the agentarea-bundle skill's references/example folder (copy it to ./shop first if you need a writable copy). Add a refunds agent to support: it reads a ticket that asks for money back, checks it against our rules (refund within 14 days if the repair failed) and writes a recommendation for me. It must never issue a refund itself. Then redeploy to the workspace corner-bikes.
