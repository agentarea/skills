---
tags: [agentarea-bundle]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

My personal assistant agent lives in my workspace `me`, deployed from a bundle folder. My company runs in a different workspace, `northwind-ops`, with its own bundle and a CEO agent there. I want my assistant to be able to ask that CEO agent how the week is going. Can I just add the CEO under delegates in my assistant's file? How do I set this up so it survives redeploys?
