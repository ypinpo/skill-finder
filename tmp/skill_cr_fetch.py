import sys, json, urllib.request, base64

paths = [
    ("Shubhamsaboo", "awesome-llm-apps", "awesome-agent-skills/code-reviewer"),
    ("Shubhamsaboo", "awesome-llm-apps", "skills/code-reviewer"),
    ("Shubhamsaboo", "awesome-llm-apps", "code-reviewer"),
    ("Shubhamsaboo", "awesome-llm-apps", ".claude/skills/code-reviewer"),
]

for org, repo, path in paths:
    url = f"https://api.github.com/repos/{org}/{repo}/contents/{path}/SKILL.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        content = base64.b64decode(data["content"]).decode("utf-8")
        print(f"✅ {path}/SKILL.md ({len(content)} chars)")
        print(content[:1500])
        break
    except Exception as e:
        print(f"❌ {path}: {e}")
