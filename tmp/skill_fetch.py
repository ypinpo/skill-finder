import sys, json, urllib.request, base64

def fetch_skill(org, repo, path):
    url = f"https://api.github.com/repos/{org}/{repo}/contents/{path}/SKILL.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes-skill-finder"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        content = base64.b64decode(data["content"]).decode("utf-8")
        print(f"\n{'='*60}")
        print(f"  {org}/{repo} — {path}/SKILL.md")
        print(f"{'='*60}")
        print(content[:3000])
        if len(content) > 3000:
            print(f"\n... (truncated, total {len(content)} chars)")
    except Exception as e:
        print(f"\n  ERROR {org}/{repo}: {e}")

# agent-self-improvement by v8/v8
fetch_skill("v8", "v8", "agents/skills/agent-self-improvement")

# self-improving-systems by ooiyeefei/ccc
fetch_skill("ooiyeefei", "ccc", "skills/self-improving-systems")

# ai-skill by NeverSight
fetch_skill("NeverSight", "learn-skills.dev", "data/skills-md/1-skill/ai-skill/ai-skill")
