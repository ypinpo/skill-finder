import sys, json, urllib.request

installed = [
    "brainstorming","safe-code-edit","writing-skills","hermes-agent-skill-authoring",
    "systematic-debugging","test-driven-development","plan","spike","verification-before-completion",
    "skill-finder","hermes-agent","hermes-mcp-setup","hermes-memory-setup",
    "hermes-profile-management","profile-management","obsidian","codebase-understanding",
    "mcp-builder","github-pr-workflow","github-code-review","requesting-code-review",
    "simplify-code","chinese-documentation","chinese-technical-writing"
]

def search_and_filter(q, label, n=5):
    url = f"https://skillsmp.com/api/v1/skills/search?q={urllib.request.quote(q)}&sortBy=stars&limit={n}"
    resp = urllib.request.urlopen(url, timeout=15)
    data = json.loads(resp.read())
    skills = data.get("data", {}).get("skills", [])
    results = []
    for s in skills:
        name = s.get("name", "")
        if name in installed:
            continue
        if s.get("stars", 0) < 10:
            continue
        results.append({
            "name": name, "stars": s.get("stars", 0),
            "desc": (s.get("description", "") or "")[:130],
            "author": s.get("author", ""), "gh": s.get("githubUrl", "")
        })
    print(f"\n--- {label} ---")
    for i, r in enumerate(results[:3]):
        heat = "🔥" if r['stars']>=1000 else ("🟢" if r['stars']>=100 else "🟡")
        print(f"{i+1}. {r['name']}  {heat} ⭐{r['stars']:,}  | {r['author']}")
        print(f"   {r['desc']}")

# Better targeted queries based on user's actual activity
search_and_filter("agent monitoring observability logging", "📊 Agent 监控与日志")
search_and_filter("knowledge management PKM second brain notes", "🧠 知识管理")
search_and_filter("automated testing regression CI", "🧪 自动化测试")
