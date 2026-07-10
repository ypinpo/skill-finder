import sys, json, urllib.request

queries = [
    "awesome agent skills",
    "awesome claude skills codex", 
    "awesome LLM agent tools",
    "best agent skills collection",
]

for q in queries:
    url = f"https://skillsmp.com/api/v1/skills/search?q={urllib.request.quote(q)}&sortBy=stars&limit=5"
    resp = urllib.request.urlopen(url, timeout=15)
    data = json.loads(resp.read())
    skills = data.get("data", {}).get("skills", [])
    print(f"\n--- {q} ---")
    for s in skills[:3]:
        name = s.get("name", "?")
        stars = s.get("stars", 0)
        author = s.get("author", "?")
        desc = (s.get("description", "") or "")[:120]
        gh = s.get("githubUrl", "")
        print(f"  {name} ⭐{stars:,} | {author}")
        print(f"  {gh}")
