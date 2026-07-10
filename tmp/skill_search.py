import sys, json, urllib.request

queries = [
    "agent self improvement workflow",
    "context memory personalization agent", 
    "agent automation coding productivity",
]

for q in queries:
    url = f"https://skillsmp.com/api/v1/skills/search?q={urllib.request.quote(q)}&sortBy=stars&limit=8"
    try:
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read())
        print(f"\n=== {q} ===")
        if isinstance(data, list):
            for i, s in enumerate(data[:8]):
                name = s.get("name", "?")
                stars = s.get("stars", 0)
                creator = s.get("creator", "?")
                desc = (s.get("description", "") or "")[:150]
                print(f"  {i+1}. {name} ⭐{stars} | {creator}")
                print(f"     {desc}")
        else:
            print(f"  Unexpected: {type(data)}")
    except Exception as e:
        print(f"\n=== {q} === ERROR: {e}")
