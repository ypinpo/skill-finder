import sys, json, urllib.request

url = "https://api.github.com/repos/Shubhamsaboo/awesome-llm-apps/contents/"
req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read())
for item in data:
    if item["type"] == "dir" and ("skill" in item["name"].lower() or "agent" in item["name"].lower()):
        print(f"📁 {item['name']}/")
