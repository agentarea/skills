#!/usr/bin/env python3
"""Search the public AgentArea catalog: bundles, agents, MCP servers and skills.

The same catalog agentarea.ai shows and AgentArea workspaces install from.
Files are downloaded once and cached for a day in ~/.cache/agentarea-catalog.

    catalog_search.py <kind> <words...> [--limit N] [--market CODE]

kind: bundles | agents | mcp | skills | all
words: what the thing should do, in English and in the user's language
       (e.g. tender procurement rfp bid). Any word may match; more matches rank higher.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = os.environ.get(
    "AGENTAREA_CATALOG_URL",
    "https://agentarea-mcp-registry.s3.amazonaws.com/registry/system",
)
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "agentarea-catalog"
TTL = 24 * 3600


def fetch(path: str) -> bytes:
    target = CACHE / path.replace("/", "__")
    if target.exists() and time.time() - target.stat().st_mtime < TTL:
        return target.read_bytes()
    with urllib.request.urlopen(f"{BASE}/{path}", timeout=120) as response:
        data = response.read()
    CACHE.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return data


def load(path: str):
    return json.loads(fetch(path))


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[\w]+", text.lower()))


def score(words: list[str], *fields: str) -> int:
    haystack = " ".join(f for f in fields if f).lower()
    found = tokens(haystack)
    total = 0
    for word in words:
        if word in found:
            total += 3
        elif len(word) >= 4 and word in haystack:
            total += 1
    return total


def ranked(rows, limit):
    rows = [r for r in rows if r[0] > 0]
    rows.sort(key=lambda r: -r[0])
    return [r[1] for r in rows[:limit]]


def search_bundles(words, limit, market):
    out = []
    for b in load("bundles.json")["bundles"]:
        meta = b.get("metadata") or {}
        s = score(words, b.get("name", ""), b.get("display_name", ""), b.get("description", ""),
                  meta.get("category", ""), " ".join(meta.get("capabilities") or []))
        out.append((s, {
            "kind": "bundle",
            "name": b.get("name"),
            "title": b.get("display_name"),
            "description": b.get("description"),
            "agents": [a.get("name") for a in b.get("agents") or []],
            "mcps": [m.get("name") or m.get("key") for m in b.get("mcps") or []],
            "skills": [k.get("name") or k.get("key") for k in b.get("skills") or []],
            "automations": [a.get("name") or a.get("key") for a in b.get("automations") or []],
            "setup": [f.get("key") for f in b.get("setup") or []],
        }))
    return ranked(out, limit)


def search_agents(words, limit, market):
    out = []
    for a in load("agents.json")["agents"]:
        s = score(words, a.get("name", ""), a.get("description", ""), " ".join(a.get("tags") or []),
                  a.get("instruction", ""))
        out.append((s, {
            "kind": "agent",
            "name": a.get("name"),
            "description": a.get("description"),
            "tags": a.get("tags"),
            "tools": [t.get("name") for t in a.get("tools") or []],
            "skills": a.get("skills"),
        }))
    return ranked(out, limit)


def search_mcp(words, limit, market):
    out = []
    for m in load("mcp-servers.json")["servers"]:
        audience = m.get("audience")
        if audience and market and market not in audience:
            continue
        raw = ((m.get("json_spec") or {}).get("raw_spec")) or {}
        s = score(words, m.get("name", ""), raw.get("title", ""), m.get("description", ""))
        if s == 0:
            continue
        remote = bool(raw.get("remotes")) or m.get("transport") in ("streamable-http", "sse")
        out.append((s, {
            "kind": "mcp",
            "name": m.get("name"),
            "title": raw.get("title"),
            "description": m.get("description"),
            "connection_type": m.get("connection_type"),
            "hosting": "vendor-hosted" if remote else "package (platform runs it)",
            "audience": audience,
            "repository": (raw.get("repository") or {}).get("url"),
        }))
    return ranked(out, limit)


def search_skills(words, limit, market):
    lookup = load("skills/lookup.json")
    hits = ranked([(score(words, skill_id.replace("-", " ")), skill_id) for skill_id in lookup],
                  limit * 4)
    pages: dict[int, dict] = {}
    out = []
    for skill_id in hits:
        page = lookup[skill_id]
        if page not in pages:
            pages[page] = {s["id"]: s for s in load(f"skills/pages/page-{page}.json")["skills"]}
        s = pages[page].get(skill_id)
        if not s:
            continue
        out.append((score(words, s.get("name", ""), s.get("description", ""), skill_id)
                    + min(s.get("stars") or 0, 50000) // 10000, {
            "kind": "skill",
            "id": skill_id,
            "name": s.get("name"),
            "description": (s.get("description") or "")[:240],
            "source": s.get("repo_url"),
            "install": s.get("install_command"),
            "stars": s.get("stars"),
        }))
    return ranked(out, limit)


SEARCHERS = {
    "bundles": search_bundles,
    "agents": search_agents,
    "mcp": search_mcp,
    "skills": search_skills,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=[*SEARCHERS, "all"])
    parser.add_argument("words", nargs="+")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--market", help="market code: drop MCP servers published only for other markets")
    args = parser.parse_args()

    words = sorted({w for phrase in args.words for w in tokens(phrase)})
    kinds = list(SEARCHERS) if args.kind == "all" else [args.kind]
    result = {}
    for kind in kinds:
        try:
            result[kind] = SEARCHERS[kind](words, args.limit, args.market)
        except Exception as exc:  # one unreachable file must not hide the others
            result[kind] = {"error": f"{type(exc).__name__}: {exc}"}
    json.dump(result, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
