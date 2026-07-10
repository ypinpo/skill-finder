import sys, json, urllib.request

installed = [
    "brainstorming","safe-code-edit","writing-skills","hermes-agent-skill-authoring",
    "systematic-debugging","test-driven-development","plan","spike","verification-before-completion",
    "skill-finder","hermes-agent","hermes-desktop","hermes-mcp-setup","hermes-memory-setup",
    "hermes-profile-management","profile-management","obsidian","codebase-understanding"
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
        results.append({
            "name": name,
            "stars": s.get("stars", 0),
            "desc": (s.get("description", "") or "")[:140],
            "author": s.get("author", ""),
            "gh": s.get("githubUrl", "")
        })
    print(f"\n--- {label} ---")
    for i, r in enumerate(results[:3]):
        print(f"{i+1}. {r['name']}  ⭐{r['stars']:,}  | {r['author']}")
        print(f"   {r['desc']}")
        print(f"   📦 {r['gh']}")

# Domain 1: Agent/Ops (based on recent heavy Hermes activity)
search_and_filter("agent orchestration workflow multi-agent", "🔧 Agent 编排与工作流")
# Domain 2: MCP/Tool integration
search_and_filter("MCP server development tool integration", "🧩 MCP 工具集成")
# Domain 3: Quality/code (based on developer background)
search_and_filter("agent code quality review documentation", "💻 代码质量与文档")
