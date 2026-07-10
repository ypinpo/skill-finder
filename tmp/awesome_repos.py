import sys, json, urllib.request

repos = [
    ("gmh5225", "awesome-skills"),
    ("kodustech", "awesome-agent-skills"),
    ("EgoAlpha", "awesome-DeepAgent-skills"),
    ("junminhong", "awesome-agent-skills"),
]

for org, repo in repos:
    url = f"https://api.github.com/repos/{org}/{repo}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        print(f"{org}/{repo}: ⭐{data['stargazers_count']:,} | {data['description'][:100] if data.get('description') else 'N/A'}")
    except Exception as e:
        print(f"{org}/{repo}: ERROR {e}")
