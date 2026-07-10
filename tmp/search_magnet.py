#!/usr/bin/env python3
"""搜索磁力链接 - 纯 Python，仅依赖标准库"""
import urllib.request, urllib.parse, re, html, ssl, json

# 忽略 SSL 证书错误（百度可能有问题）
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12, context=ssl_ctx) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        return None

def search_baidu(keyword, max_n=5):
    url = f"https://www.baidu.com/s?wd={urllib.parse.quote(keyword)}&rn={max_n*2}"
    data = fetch(url)
    if not data:
        return []
    
    results = []
    # 方法1: 匹配 h3 中的链接
    for m in re.finditer(r'<h3[^>]*>.*?<a[^>]*href="(https?://[^"]*baidu[^"]*link[^"]*)"[^>]*>(.*?)</a>', data, re.DOTALL):
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        results.append({'title': title, 'link': m.group(1), 'source': 'baidu'})
    
    # 方法2: 匹配更简单的格式
    for m in re.finditer(r'<a[^>]*href="(https?://[^"]*)"[^>]*data-click="[^"]*"[^>]*>(.*?)</a>', data, re.DOTALL):
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        link = m.group(1)
        if title and len(title) > 5 and 'baidu' not in link:
            results.append({'title': title, 'link': link, 'source': 'baidu'})
    
    return results[:max_n]

def search_sogou(keyword, max_n=5):
    url = f"https://www.sogou.com/web?query={urllib.parse.quote(keyword)}"
    data = fetch(url)
    if not data:
        return []
    
    results = []
    for m in re.finditer(r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', data, re.DOTALL):
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        link = m.group(1)
        if title and len(title) > 5:
            results.append({'title': title, 'link': link, 'source': 'sogou'})
    return results[:max_n]

def is_magnet(item):
    t = (item['title'] + ' ').lower()
    return any(k in t for k in ['magnet', '磁力', 'btih', 'torrent', '种子'])

def search_bing(keyword, max_n=5):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(keyword)}"
    data = fetch(url)
    if not data:
        return []
    results = []
    for m in re.finditer(r'<h2[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', data, re.DOTALL):
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        link = m.group(1)
        if title and len(title) > 5:
            results.append({'title': title, 'link': link, 'source': 'bing'})
    return results[:max_n]

queries = [
    "JAV 4K 2160p 无码 磁力 种子",
    "uncensored 4K jav torrent magnet",
    "HEYZO 4K 2160p 下载 种子",
    "javdb magnet 4K uncensored",
    "磁力 猫 4K 无码 JAV",
    "btih 4K uncensored jav",
]

all_results = {}
for q in queries:
    print(f"\n{'='*60}")
    print(f"🔍 {q}")
    print('='*60)
    
    b = search_baidu(q, 5)
    s = search_sogou(q, 5)
    
    combined = b + s
    if not combined:
        print("  (无结果)")
        continue
    
    for item in combined:
        tag = {'baidu': 'B', 'sogou': 'S'}.get(item['source'], '?')
        m = ' ⭐磁力' if is_magnet(item) else ''
        print(f"  [{tag}] {item['title'][:80]}{m}")
        link = item['link'][:100]
        print(f"        {link}")
        # 如果是磁力链接直接输出
        if 'magnet:?' in link.lower():
            print(f"        📌 直接可用磁力链接!")
            all_results.setdefault('magnets', []).append(link)

# 也搜搜 Bing
print(f"\n{'='*60}")
print(f"🔍 Bing 搜索 magnet 链接")
print('='*60)
for q in ["magnet:?xt=urn:btih 4K jav", "jav uncensored 4K torrent magnet"]:
    r = search_bing(q, 5)
    for item in r:
        m = ' ⭐磁力' if is_magnet(item) else ''
        print(f"  [B] {item['title'][:80]}{m}")
        print(f"        {item['link'][:100]}")

if all_results.get('magnets'):
    print(f"\n\n{'🎯'*10}")
    print("找到的磁力链接:")
    for m in all_results['magnets']:
        print(f"  {m}")
