import sys, json, urllib.request

def search(q, label, n=5):
    url = f"https://skillsmp.com/api/v1/skills/search?q={urllib.request.quote(q)}&sortBy=stars&limit={n}"
    resp = urllib.request.urlopen(url, timeout=15)
    data = json.loads(resp.read())
    skills = data.get("data", {}).get("skills", [])
    print(f"\n--- {label} ---")
    for i, s in enumerate(skills):
        name = s.get("name", "?")
        stars = s.get("stars", 0)
        desc = (s.get("description", "") or "")[:120]
        gh = s.get("githubUrl", "")
        import time
        updated = int(s.get("updatedAt", "0"))
        days_ago = (time.time() - updated) // 86400 if updated else 999
        print(f"\n{i+1}. {name}  ⭐{stars:,}  (~{days_ago}天前)")
        print(f"   {desc}")
        print(f"   📦 {gh}")

# 跨领域搜索，覆盖不同方向
search("game development design", "🎮 游戏开发")
search("data science visualization analysis", "📊 数据科学")
search("video editing multimedia production", "🎬 视频/多媒体")
search("writing creative content generation", "✍️ 写作创作")
search("devops deployment automation CI CD", "⚙️ DevOps/自动化")
search("security pentest cybersecurity", "🔒 安全")
