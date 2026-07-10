import sys, json, urllib.request, base64

def fetch_skill(label, org, repo, path):
    url = f"https://api.github.com/repos/{org}/{repo}/contents/{path}/SKILL.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        content = base64.b64decode(data["content"]).decode("utf-8")
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"  {org}/{repo} — {path}/SKILL.md ({len(content)} chars)")
        print(f"{'='*60}")
        print(content[:2500])
    except Exception as e:
        print(f"\n  ERROR {label}: {e}")

# Top 3: different approaches to agent self-improvement
fetch_skill("A. agent-self-improvement (V8)", "v8", "v8", "agents/skills/agent-self-improvement")
fetch_skill("B. self-improving-agent (TeamWiseFlow)", "TeamWiseFlow", "xiaobei", "_disabled/skills/self-improving")
fetch_skill("C. autoresearch (j1ngg)", "j1ngg", "tech-marketing-framework", ".claude/skills/autoresearch")
