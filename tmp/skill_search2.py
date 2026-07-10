import sys, json, urllib.request

def search(q, label, n=8):
    url = f"https://skillsmp.com/api/v1/skills/search?q={urllib.request.quote(q)}&sortBy=stars&limit={n}"
    try:
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read())
        skills = data.get("data", {}).get("skills", [])
        print(f"\n{'='*60}")
        print(f"  {label} ({len(skills)} 结果)")
        print(f"{'='*60}")
        for i, s in enumerate(skills):
            name = s.get("name", "?")
            stars = s.get("stars", 0)
            author = s.get("author", "?")
            desc = (s.get("description", "") or "")[:140]
            gh = s.get("githubUrl", "")
            print(f"  {i+1}. {name}  ⭐{stars:,}  | {author}")
            print(f"     {desc}")
            if gh:
                print(f"     📦 {gh}")
    except Exception as e:
        print(f"\n  {label}: ERROR {e}")

# 聚焦"让Hermes更好用"的场景
search("agent workflow automation productivity", "Agent 工作流自动化", 8)
search("context management agent memory", "上下文与记忆管理", 8)
search("coding agent quality review testing", "代码质量与审查", 8)
search("agent skill management curation", "Skill 管理与发现", 8)
