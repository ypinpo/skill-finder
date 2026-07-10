import sys, json, urllib.request

url = "https://api.github.com/repos/Shubhamsaboo/awesome-llm-apps/contents/agent_skills"
req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read())
for item in data:
    print(f"  {'📁' if item['type']=='dir' else '📄'} {item['name']}")
