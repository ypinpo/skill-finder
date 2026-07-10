import sys, json, urllib.request, base64

def fetch_full(label, org, repo, path, outfile):
    url = f"https://api.github.com/repos/{org}/{repo}/contents/{path}/SKILL.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        content = base64.b64decode(data["content"]).decode("utf-8")
        with open(outfile, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {label}: {len(content)} chars → {outfile}")
        return content
    except Exception as e:
        print(f"❌ {label}: {e}")
        return None

base = "D:\\AI\\Workspace\\Hermes\\default-profile\\tmp"

# A: V8 agent-self-improvement
content_a = fetch_full("A. agent-self-improvement", "v8", "v8", 
                        "agents/skills/agent-self-improvement",
                        f"{base}\\skill_a_original.md")

# B: self-improving-agent  
content_b = fetch_full("B. self-improving-agent", "TeamWiseFlow", "xiaobei",
                        "_disabled/skills/self-improving",
                        f"{base}\\skill_b_original.md")

print("\nDone.")
