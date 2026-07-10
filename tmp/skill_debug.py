import sys, json, urllib.request

url = "https://skillsmp.com/api/v1/skills/search?q=agent+self+improvement&sortBy=stars&limit=5"
resp = urllib.request.urlopen(url, timeout=15)
data = json.loads(resp.read())
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
