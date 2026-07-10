import sys, json, urllib.request

def search(q, label, n=8):
    url = f"https://skillsmp.com/api/v1/skills/search?q={urllib.request.quote(q)}&sortBy=stars&limit={n}"
    try:
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read())
        skills = data.get("data", {}).get("skills", [])
        print(f"\n{'='*60}")
        print(f"  {label} ({len(skills)} 结果)")
        print(f"{'='*60}")
        for i, s in enumerate(skills):
            name = s.get("name", "?")
            stars = s.get("stars", 0)
            author = s.get("author", "?")
            desc = (s.get("description", "") or "")[:180]
            gh = s.get("githubUrl", "")
            print(f"  {i+1}. {name}  ⭐{stars:,}  | {author}")
            print(f"     {desc}")
            print(f"     📦 {gh}")
    except Exception as e:
        print(f"\n  {label}: ERROR {e}")

# 多角度搜索"agent自我进化"类skill
search("agent self reflection learning mistakes continuous improvement", "自我反思与持续改进")
search("agent meta cognition self correction feedback loop", "元认知与反馈闭环")
search("agent performance evaluation benchmark self test", "性能评估与自测")
search("skill optimization auto update maintain evolve", "Skill 自动优化与进化")
