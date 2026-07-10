import sys, json, urllib.request, base64

def fetch(org, repo, path, label):
    url = f"https://api.github.com/repos/{org}/{repo}/contents/{path}/SKILL.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        content = base64.b64decode(data["content"]).decode("utf-8")
        print(f"\n{'='*60}")
        print(f"  {label}  |  {org}/{repo}")
        print(f"  {path}/SKILL.md  ({len(content)} chars)")
        print(f"{'='*60}")
        print(content[:2000])
        if len(content) > 2000:
            print(f"\n... ({len(content)} total chars)")
    except Exception as e:
        print(f"\n  ❌ {label}: {e}")

fetch("Shubhamsaboo", "awesome-llm-apps", "awesome-agent-skills/code-reviewer", "🥇 code-reviewer")
fetch("anthropics", "skills", "skills/frontend-design", "🥈 frontend-design")
fetch("anthropics", "skills", "skills/docx", "🥉 docx")
