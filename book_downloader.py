#!/usr/bin/env python3
"""
批量下载英文小说 - 多源容错版
一次运行，下完为止：LibGen → Anna's Archive → Z-Library → IPFS
输出目录：D:\AI\Workspace\Hermes\harness-director\downloads
"""

import os, sys, re, time, json, hashlib, logging, random, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, List, Tuple
from urllib.parse import quote_plus

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# 可选依赖：Cloudflare 反反爬
try:
    import cloudscraper
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ── 配置 ──────────────────────────────────────────────
DOWNLOAD_DIR = Path(r"D:\AI\Workspace\Hermes\harness-director\downloads")
LOG_FILE = DOWNLOAD_DIR / "download.log"
STATE_FILE = DOWNLOAD_DIR / ".download_state.json"
CONNECT_TIMEOUT = 15
READ_TIMEOUT = 120
MAX_WORKERS = 3
GLOBAL_RETRY_ROUNDS = 3        # 全部失败后全量重跑次数
ROUND_BACKOFF_BASE = 30        # 轮间等待基数秒
MIN_FILE_SIZE_KB = 80          # 低于此大小的文件视为残损

# Windows 非法字符
_ILLEGAL_FILENAME = re.compile(r'[<>:"/\\|?*]')

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# ── 书单 ───────────────────────────────────────────────
@dataclass
class Book:
    title: str
    author: str
    category: str
    note: str = ""

BOOKS = [
    # Romantasy
    Book("A Court of Silver Flames", "Sarah J. Maas", "romantasy", "ACOTAR#5"),
    Book("From Blood and Ash", "Jennifer L. Armentrout", "romantasy", "Blood and Ash#1"),
    Book("Kushiel's Dart", "Jacqueline Carey", "romantasy", "Kushiel's Legacy#1"),
    Book("Neon Gods", "Katee Robert", "romantasy", "Dark Olympus#1"),
    Book("The Lady of Rooksgrave Manor", "Kathryn Moon", "romantasy", "Tempting Monsters#1"),
    # Sci-Fi
    Book("Project Hail Mary", "Andy Weir", "scifi", ""),
    Book("Children of Time", "Adrian Tchaikovsky", "scifi", "Children of Time#1"),
    Book("Leviathan Wakes", "James S.A. Corey", "scifi", "The Expanse#1"),
    Book("Altered Carbon", "Richard K. Morgan", "scifi", "Takeshi Kovacs#1"),
    Book("Hyperion", "Dan Simmons", "scifi", "Hyperion Cantos#1"),
]

# ── 日志 ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ── HTTP 会话工厂 ──────────────────────────────────────
def _make_session(retries=2, backoff=0.5) -> requests.Session:
    s = requests.Session()
    if PROXY:
        s.proxies = PROXY
    retry = Retry(total=retries, backoff_factor=backoff,
                  status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(HEADERS)
    return s


def _fetch(url: str, session: requests.Session, timeout=CONNECT_TIMEOUT) -> Optional[requests.Response]:
    """带 Cloudflare 降级的请求。"""
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code == 200:
            return r
        if r.status_code == 403 and "cloudflare" in r.text.lower() and HAS_SCRAPER:
            log.debug(f"Cloudflare 拦截，切换 cloudscraper: {url[:60]}")
            scr = cloudscraper.create_scraper()
            r2 = scr.get(url, timeout=timeout)
            if r2.status_code == 200:
                return r2
    except Exception:
        pass
    return None


# ── 预探测：快速筛选可达镜像 ──────────────────────────
REACHABLE = set()          # 启动时探测通过的所有镜像 base URL
PROBE_TIMEOUT = 3          # 快速探测超时（秒）
PROXY = None               # 命令行传入的代理地址

# 公共 CORS 代理（无代理软件时的降级方案）
CORS_PROXIES = [
    "https://api.allorigins.win/raw?url=",
    "https://corsproxy.io/?",
    "https://proxy.cors.sh/",
]

def _via_cors(target_url: str, session: requests.Session) -> Optional[str]:
    """通过公共 CORS 代理抓取被墙页面。逐页搜索，不用于大文件下载。"""
    for cp in CORS_PROXIES:
        try:
            r = session.get(f"{cp}{target_url}", timeout=15, headers=HEADERS)
            if r.status_code == 200 and len(r.text) > 500:
                return r.text
        except Exception:
            continue
    return None


def _probe_mirrors(mirrors: List[str], label: str) -> List[str]:
    """并发探测镜像列表，返回可达的（过滤 connect/read timeout）。"""
    good = []
    for url in mirrors:
        try:
            r = requests.head(url, timeout=PROBE_TIMEOUT, headers=HEADERS,
                              proxies=PROXY, allow_redirects=True)
            if r.status_code < 500:
                good.append(url)
                REACHABLE.add(url)
                log.info(f"  [可达] {label}: {url}")
            else:
                log.warning(f"  [不可达] {label}: {url} (HTTP {r.status_code})")
        except Exception:
            log.warning(f"  [超时] {label}: {url}")
    return good


# ── 文件名 ─────────────────────────────────────────────
def _safe_filename(title: str, ext: str) -> str:
    safe = _ILLEGAL_FILENAME.sub("_", title)
    safe = safe.replace(":", "").replace("'", "")
    safe = re.sub(r'\s+', ' ', safe).strip()
    if len(safe) > 120:
        safe = safe[:120]
    return f"{safe}{ext}"


# ═══════════════════════════════════════════════════════
#  书源：LibGen Fiction
# ═══════════════════════════════════════════════════════
LG_FICTION_MIRRORS = [
    "https://libgen.is",
    "https://libgen.li",
    "https://libgen.st",
    "https://libgen.gs",
    "https://libgen.rs",
]

def source_libgen_fiction(book: Book, session: requests.Session) -> Optional[str]:
    mirrors = [m for m in LG_FICTION_MIRRORS if m in REACHABLE]
    if not mirrors:
        log.debug("LibGen Fiction 无可达镜像，跳过")
        return None
    query = quote_plus(f"{book.title} {book.author}")
    for base in mirrors:
        url = f"{base}/fiction/search?q={query}&format=json"
        r = _fetch(url, session)
        if not r:
            continue
        try:
            results = r.json()
        except Exception:
            continue
        if not results:
            continue
        # 按文件大小 + 语言为英语优先排序
        scored = []
        for item in results:
            lang = (item.get("language") or "").lower()
            size = int(item.get("filesize") or 0)
            score = size + (100_000_000 if lang == "english" else 0)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]
        md5 = best.get("md5")
        if not md5:
            continue
        title_found = best.get("title", "?")
        lang_found = best.get("language", "?")
        dl = f"{base}/fiction/get/{md5}"
        log.info(f"  [LG-Fiction] {title_found} ({lang_found})")
        return dl
    return None


# ═══════════════════════════════════════════════════════
#  书源：LibGen Non-Fiction
# ═══════════════════════════════════════════════════════
LG_NONFIC_MIRRORS = [
    "https://libgen.is",
    "https://libgen.li",
    "https://libgen.st",
]

def source_libgen_nonfiction(book: Book, session: requests.Session) -> Optional[str]:
    mirrors = [m for m in LG_NONFIC_MIRRORS if m in REACHABLE]
    if not mirrors:
        log.debug("LibGen NonFic 无可达镜像，跳过")
        return None
    query = quote_plus(f"{book.title} {book.author}")
    for base in mirrors:
        url = f"{base}/search.php?req={query}&open=0&res=25&view=simple&phrase=1&column=def"
        r = _fetch(url, session)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table.c tr, table[class] tr")
        candidates = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 10:
                continue
            try:
                title_cell = cells[2]
                link = title_cell.find("a", href=True)
                if not link:
                    continue
                href = link["href"]
                if "book/index.php?md5=" not in href:
                    continue
                md5 = href.split("md5=")[-1].split("&")[0].upper()
                ext = (cells[8].get_text(strip=True) or "").lower()
                size_str = cells[7].get_text(strip=True) or "0"
                size = int(size_str) if size_str.isdigit() else 0
                if ext in ("epub", "pdf", "mobi"):
                    candidates.append((size, md5, ext))
            except Exception:
                continue
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            _, md5, ext = candidates[0]
            dl = f"{base}/book/index.php?md5={md5}"
            log.info(f"  [LG-NonFic] {ext.upper()} ({candidates[0][0]//1024}KB)")
            return dl
    return None


# ═══════════════════════════════════════════════════════
#  书源：Anna's Archive
# ═══════════════════════════════════════════════════════
AA_MIRRORS = [
    "https://annas-archive.gd",
    "https://annas-archive.se",
    "https://annas-archive.org",
]

def _aa_search(book: Book, session: requests.Session) -> Optional[str]:
    mirrors = [m for m in AA_MIRRORS if m in REACHABLE]
    if not mirrors:
        log.debug("Anna's Archive 无可达镜像，跳过")
        return None
    query = quote_plus(f"{book.title} {book.author}")
    for base in mirrors:
        url = f"{base}/search?q={query}"
        r = _fetch(url, session)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a_tag in soup.select("a[href^='/md5/']"):
            return f"{base}{a_tag['href']}"
    return None


def _aa_extract_download(detail_url: str, session: requests.Session) -> Optional[str]:
    r = _fetch(detail_url, session)
    if not r:
        return None
    soup = BeautifulSoup(r.text, "html.parser")

    # 策略1：查找包含 "download" 文本且指向外部 URL 的链接
    for a_tag in soup.select("a[href^='http']"):
        text = a_tag.get_text(strip=True).lower()
        href = a_tag["href"]
        if any(kw in text for kw in ("download", "slow", ".epub", ".pdf")):
            if any(href.endswith(ext) for ext in (".epub", ".pdf", ".mobi")):
                return href
            # 也可能是重定向链接
            if "annas-archive" not in href and "cloudflare" not in href:
                return href

    # 策略2：找 /slow_download/ 路径
    for a_tag in soup.select("a[href*='/slow_download/']"):
        href = a_tag["href"]
        if href.startswith("/"):
            # 需要拼接域名
            for base in AA_MIRRORS:
                if base in detail_url:
                    full = f"{base}{href}"
                    # 跟随重定向获取真实直链
                    try:
                        r2 = session.head(full, allow_redirects=True, timeout=CONNECT_TIMEOUT)
                        if r2.url and any(r2.url.endswith(e) for e in (".epub", ".pdf", ".mobi")):
                            return r2.url
                    except Exception:
                        pass
                    return full

    # 策略3：找任何 .epub/.pdf 直链
    for a_tag in soup.select("a[href$='.epub'], a[href$='.pdf']"):
        return a_tag["href"]

    return None


def source_annas_archive(book: Book, session: requests.Session) -> Optional[str]:
    detail = _aa_search(book, session)
    if not detail:
        return None
    dl = _aa_extract_download(detail, session)
    if dl:
        log.info(f"  [Anna's] {book.title}")
    return dl


# ═══════════════════════════════════════════════════════
#  书源：Z-Library（无需登录的公开接口）
# ═══════════════════════════════════════════════════════
ZLIB_MIRRORS = [
    "https://z-lib.gd",
    "https://z-lib.id",
    "https://singlelogin.re",
]

def source_zlib(book: Book, session: requests.Session) -> Optional[str]:
    mirrors = [m for m in ZLIB_MIRRORS if m in REACHABLE]
    if not mirrors:
        log.debug("Z-Library 无可达镜像，跳过")
        return None
    query = quote_plus(f"{book.title} {book.author}")
    for base in mirrors:
        url = f"{base}/s/{query}"
        r = _fetch(url, session)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        # 结果列表中的书籍链接
        for item in soup.select("a[href*='/book/']"):
            href = item.get("href", "")
            if "/book/" in href:
                detail_url = f"{base}{href}" if href.startswith("/") else href
                # 进详情页找下载
                r2 = _fetch(detail_url, session)
                if not r2:
                    continue
                s2 = BeautifulSoup(r2.text, "html.parser")
                for dl_a in s2.select("a[href*='download']"):
                    dl_href = dl_a.get("href", "")
                    if dl_href.startswith("http"):
                        return dl_href
                    if dl_href.startswith("/"):
                        return f"{base}{dl_href}"
    return None


# ═══════════════════════════════════════════════════════
#  书源：IPFS 直链（通过 Anna's Archive 的 IPFS 网关）
# ═══════════════════════════════════════════════════════
IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs",
    "https://cloudflare-ipfs.com/ipfs",
    "https://dweb.link/ipfs",
]

def source_ipfs(book: Book, session: requests.Session) -> Optional[str]:
    """通过 Anna's Archive 的 IPFS CID 直链下载。"""
    # 先通过 Anna's Archive 搜索获取 MD5
    detail = _aa_search(book, session)
    if not detail:
        return None
    r = _fetch(detail, session)
    if not r:
        return None
    soup = BeautifulSoup(r.text, "html.parser")

    # 找 IPFS 链接
    for a_tag in soup.select("a[href*='ipfs']"):
        href = a_tag.get("href", "")
        if "/ipfs/" in href:
            match = re.search(r'/ipfs/([a-zA-Z0-9]+)', href)
            if match:
                cid = match.group(1)
                for gw in IPFS_GATEWAYS:
                    base = "/".join(gw.split("/")[:3])
                    if base in REACHABLE:
                        return f"{gw}/{cid}"
    return None


# ═══════════════════════════════════════════════════════
#  书源：BT 磁力搜索 + aria2 DHT 下载（抗墙）
# ═══════════════════════════════════════════════════════
import subprocess
import shutil

ARIA2 = shutil.which("aria2c") or "aria2c"

def _search_magnet(book: Book, session: requests.Session) -> Optional[str]:
    """通过 CORS 代理搜索 BT 索引站找磁力链接。"""
    query = quote_plus(f"{book.title} {book.author} epub")
    # 用 btdig.com 搜索（全球最大 BT DHT 索引）
    search_urls = [
        f"https://btdig.com/search?q={query}",
        f"https://www.btdig.com/search?q={query}",
    ]
    for url in search_urls:
        html = _via_cors(url, session)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        # btdig 的磁力链接在 href 中包含 magnet:?xt=urn:btih:
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("magnet:?xt=urn:btih:"):
                return href
        # 备选：找 info_hash 拼接磁力链接
        for a_tag in soup.find_all("a", href=True):
            m = re.search(r'btih:([a-fA-F0-9]{40})', a_tag.get("href", ""))
            if m:
                return f"magnet:?xt=urn:btih:{m.group(1)}"
    return None


def source_magnet(book: Book, session: requests.Session) -> Optional[str]:
    """搜索磁力链接，找到后标记为特殊协议供 aria2 下载。"""
    magnet = _search_magnet(book, session)
    if magnet:
        log.info(f"  [Magnet] {book.title}")
        return f"magnet::{magnet}"  # 用 magnet:: 前缀区分子进程下载
    return None


def _download_magnet(magnet_url: str, filepath: Path, book: Book) -> bool:
    """使用 aria2c 下载磁力链接（DHT 网络，不依赖 tracker）。"""
    magnet = magnet_url.replace("magnet::", "")
    # 先下载到临时目录，完成后移动到目标
    tmp_dir = filepath.parent / ".aria2_tmp"
    tmp_dir.mkdir(exist_ok=True)

    cmd = [
        ARIA2, magnet,
        "-d", str(tmp_dir),
        "--bt-metadata-only=false",
        "--enable-dht=true",
        "--enable-dht6=false",
        "--dht-listen-port=6881-6999",
        "--bt-enable-lpd=true",
        "--seed-time=0",
        "--max-connection-per-server=16",
        "--split=16",
        "--max-concurrent-downloads=1",
        "--console-log-level=warn",
        "--bt-stop-timeout=300",          # 5 分钟内没新节点就停止
        "--timeout=30",
        "--connect-timeout=15",
    ]
    log.info(f"  启动 aria2c DHT 下载 ...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        # aria2c 把文件下到 tmp_dir 里，找出来
        downloaded = list(tmp_dir.glob("*"))
        # 排除 .aria2 控制文件和目录
        files = [f for f in downloaded if f.is_file() and f.suffix != ".aria2"]
        if files:
            # 优先 epub，其次 pdf
            epub = [f for f in files if f.suffix.lower() == ".epub"]
            target = epub[0] if epub else files[0]
            shutil.move(str(target), str(filepath))
            # 清理其他文件
            for f in files:
                if f.exists():
                    f.unlink()
            return True
        return False
    except subprocess.TimeoutExpired:
        log.warning(f"  aria2 超时（10分钟）")
        return False
    except Exception as e:
        log.warning(f"  aria2 异常: {e}")
        return False


# ═══════════════════════════════════════════════════════
#  书源：CORS 代理降级（无翻墙时的最后一搏）
# ═══════════════════════════════════════════════════════
def source_cors_fallback(book: Book, session: requests.Session) -> Optional[str]:
    """通过公共 CORS 代理搜索 Anna's Archive，再尝试直连下载。"""
    query = quote_plus(f"{book.title} {book.author}")
    # 只用 Anna's .org 搜（因为走 CORS 代理，不关心域名是否可达）
    search_url = f"https://annas-archive.org/search?q={query}"
    html = _via_cors(search_url, session)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    md5_link = None
    for a_tag in soup.select("a[href^='/md5/']"):
        md5_link = a_tag["href"]
        break

    if not md5_link:
        md5_link = None
        for a_tag in soup.find_all("a", href=True):
            if "/md5/" in a_tag["href"]:
                md5_link = a_tag["href"]
                break

    if not md5_link:
        return None

    # 详情页也走 CORS
    detail_html = _via_cors(f"https://annas-archive.org{md5_link}", session)
    if not detail_html:
        return None

    d_soup = BeautifulSoup(detail_html, "html.parser")
    # 找下载链接：slow_download 或直链
    for a_tag in d_soup.select("a[href*='slow_download']"):
        return f"https://annas-archive.org{a_tag['href']}"

    for a_tag in d_soup.select("a[href$='.epub'], a[href$='.pdf']"):
        return a_tag["href"]

    # 最后尝试：搜 IPFS 链接（如果能拿到 CID，走 IPFS 网关）
    for a_tag in d_soup.select("a[href*='/ipfs/']"):
        match = re.search(r'/ipfs/([a-zA-Z0-9]+)', a_tag.get("href", ""))
        if match:
            cid = match.group(1)
            for gw in IPFS_GATEWAYS:
                return f"{gw}/{cid}"

    return None


# ═══════════════════════════════════════════════════════
#  下载引擎
# ═══════════════════════════════════════════════════════
SOURCES = [
    ("LibGen-Fiction", source_libgen_fiction),
    ("LibGen-NonFiction", source_libgen_nonfiction),
    ("Anna's-Archive", source_annas_archive),
    ("Z-Library", source_zlib),
    ("IPFS", source_ipfs),
    ("Magnet-BT", source_magnet),
    ("CORS-Fallback", source_cors_fallback),
]


def _download_with_progress(url: str, filepath: Path, book: Book) -> bool:
    """流式下载 + 可选进度条 + 断点续传。直连失败时自动走 CORS 代理。"""
    headers = {**HEADERS}
    resumed_bytes = 0

    if filepath.exists():
        resumed_bytes = filepath.stat().st_size
        if resumed_bytes > MIN_FILE_SIZE_KB * 1024:
            return True
        headers["Range"] = f"bytes={resumed_bytes}-"

    # 尝试直连
    session = _make_session(retries=1, backoff=0.5)
    r = _try_download(session, url, headers, filepath, book, resumed_bytes)
    if r:
        return True

    # 直连失败 → CORS 代理降级
    log.debug(f"  直连失败，尝试 CORS 代理...")
    session2 = _make_session(retries=0, backoff=0)
    for cp in CORS_PROXIES:
        try:
            log.debug(f"  CORS: {cp[:30]}...")
            r2 = session2.get(f"{cp}{url}", timeout=READ_TIMEOUT, stream=True,
                              headers={"User-Agent": HEADERS["User-Agent"]})
            if r2.status_code == 200:
                total = int(r2.headers.get("content-length", 0))
                if total < MIN_FILE_SIZE_KB * 1024:
                    continue  # 太小，可能是错误页面
                with open(filepath, "wb") as f:
                    if HAS_TQDM and total > 0:
                        desc = _safe_filename(book.title, "")[:30]
                        pbar = tqdm(total=total, unit="B", unit_scale=True, desc=desc, leave=False)
                        for chunk in r2.iter_content(chunk_size=8192):
                            f.write(chunk); pbar.update(len(chunk))
                        pbar.close()
                    else:
                        for chunk in r2.iter_content(chunk_size=8192):
                            f.write(chunk)
                return True
        except Exception:
            continue

    return False


def _try_download(session, url, headers, filepath, book, resumed):
    """单次直连下载尝试。"""
    try:
        r = session.get(url, headers=headers, timeout=READ_TIMEOUT, stream=True)
        if r.status_code not in (200, 206):
            return False

        total = int(r.headers.get("content-length", 0))
        mode = "ab" if r.status_code == 206 else "wb"

        if HAS_TQDM and total > 0:
            desc = _safe_filename(book.title, "")[:30]
            pbar = tqdm(total=total, unit="B", unit_scale=True, desc=desc, leave=False)
        else:
            pbar = None

        with open(filepath, mode) as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    if pbar:
                        pbar.update(len(chunk))

        if pbar:
            pbar.close()

        # 校验大小
        if total > 0:
            actual = filepath.stat().st_size
            if actual < total * 0.95:  # 允许 5% 冗余（压缩差异）
                log.warning(f"  文件可能不完整: {actual} / {total} bytes")
                return False

        return True

    except Exception as e:
        log.debug(f"  下载异常: {e}")
        return False


def download_book(book: Book) -> bool:
    """下载单本书：遍历所有源，直到成功。"""
    ext = ".epub"
    filename = _safe_filename(book.title, ext)
    filepath = DOWNLOAD_DIR / filename

    # 已完成跳过
    if filepath.exists() and filepath.stat().st_size > MIN_FILE_SIZE_KB * 1024:
        log.info(f"[✓] {book.title} — 已存在")
        return True

    log.info(f"[→] {book.category.upper()}: {book.title} ({book.author})")

    session = _make_session()

    for src_name, src_func in SOURCES:
        try:
            dl_url = src_func(book, session)
            if not dl_url:
                continue

            # 磁力链接：走 aria2 DHT 下载
            if dl_url.startswith("magnet::"):
                log.info(f"  下载中 [{src_name}] — aria2 DHT ...")
                if _download_magnet(dl_url, filepath, book):
                    size_kb = filepath.stat().st_size // 1024
                    log.info(f"[✓] {book.title} → {filename} ({size_kb} KB) [{src_name}]")
                    return True
                else:
                    log.warning(f"  下载失败 [{src_name}]，尝试下一个源...")
                    if filepath.exists():
                        filepath.unlink()
                continue

            # 根据 URL 后缀修正扩展名
            if dl_url.endswith(".pdf"):
                ext = ".pdf"
                filename = _safe_filename(book.title, ext)
                filepath = DOWNLOAD_DIR / filename
            elif dl_url.endswith(".mobi"):
                ext = ".mobi"
                filename = _safe_filename(book.title, ext)
                filepath = DOWNLOAD_DIR / filename

            log.info(f"  下载中 [{src_name}]...")
            if _download_with_progress(dl_url, filepath, book):
                size_kb = filepath.stat().st_size // 1024
                log.info(f"[✓] {book.title} → {filename} ({size_kb} KB) [{src_name}]")
                return True
            else:
                log.warning(f"  下载失败 [{src_name}]，尝试下一个源...")
                # 删除残损文件
                if filepath.exists():
                    filepath.unlink()

        except Exception as e:
            log.debug(f"  {src_name} 异常: {e}")
            continue

    log.error(f"[✗] {book.title} — 所有源均失败")
    return False


# ── 主流程 ─────────────────────────────────────────────
def _load_state() -> List[str]:
    """加载已完成的书名列表。"""
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data.get("completed", [])
        except Exception:
            pass
    return []


def _save_state(completed: List[str]):
    STATE_FILE.write_text(
        json.dumps({"completed": completed, "updated": time.strftime("%Y-%m-%d %H:%M:%S")},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main():
    global PROXY

    ap = argparse.ArgumentParser(description="批量下载英文小说")
    ap.add_argument("--proxy", metavar="URL",
                    help="代理地址，如 socks5://127.0.0.1:10808 或 http://127.0.0.1:7890")
    ap.add_argument("--no-probe", action="store_true",
                    help="跳过启动探测，直接尝试所有镜像")
    args = ap.parse_args()

    # 优先级：命令行 > 环境变量 HTTPS_PROXY
    PROXY = {"http": args.proxy, "https": args.proxy} if args.proxy else None

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if not args.no_probe:
        log.info("启动前镜像探测 ...")
        all_lg = list(dict.fromkeys(LG_FICTION_MIRRORS + LG_NONFIC_MIRRORS))
        _probe_mirrors(all_lg, "LibGen")
        _probe_mirrors(AA_MIRRORS, "Anna's")
        _probe_mirrors(ZLIB_MIRRORS, "Z-Lib")
        _probe_mirrors(["/".join(gw.split("/")[:3]) for gw in IPFS_GATEWAYS], "IPFS")
        log.info(f"探测完成，可达镜像: {len(REACHABLE)} 个")

        if not REACHABLE:
            msg = (
                "\n⚠️  所有书源镜像均不可达（可能被墙/网络不通）。\n"
                "    请尝试：\n"
                f"    python {Path(__file__).name} --proxy socks5://127.0.0.1:端口\n"
                "    或设置环境变量：set HTTPS_PROXY=http://127.0.0.1:端口\n"
            )
            log.warning(msg)
            return

    log.info("=" * 60)
    log.info(f"目标目录: {DOWNLOAD_DIR}")
    log.info(f"书单: Romantasy ×5 | 科幻 ×5 | 共 {len(BOOKS)} 本")
    log.info(f"源链: {' → '.join(s[0] for s in SOURCES)}")
    log.info(f"最大重跑轮次: {GLOBAL_RETRY_ROUNDS}")
    log.info(f"Cloudflare 反反爬: {'可用' if HAS_SCRAPER else '不可用'}")
    log.info(f"进度条: {'可用' if HAS_TQDM else '不可用'}")
    log.info("=" * 60)

    completed = set(_load_state())
    pending = [b for b in BOOKS if b.title not in completed]
    all_failed = []

    for round_num in range(1, GLOBAL_RETRY_ROUNDS + 1):
        if not pending:
            break

        if round_num > 1:
            wait = ROUND_BACKOFF_BASE * (2 ** (round_num - 2))
            log.info(f"\n--- 第 {round_num} 轮重试，等待 {wait}s ---")
            time.sleep(wait)

        round_failed = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(download_book, b): b for b in pending}
            for future in as_completed(futures):
                book = futures[future]
                try:
                    if future.result():
                        completed.add(book.title)
                        _save_state(list(completed))
                    else:
                        round_failed.append(book)
                except Exception as e:
                    log.error(f"[!] {book.title}: {e}")
                    round_failed.append(book)

        pending = round_failed
        all_failed = [b.title for b in round_failed]

        if pending:
            log.info(f"本轮剩余 {len(pending)} 本未完成: {', '.join(b.title for b in pending)}")

    # ── 汇总 ──
    log.info("\n" + "=" * 60)
    success_count = len(completed)
    fail_count = len(all_failed)
    log.info(f"最终结果: 成功 {success_count} / 失败 {fail_count} / 总计 {len(BOOKS)}")
    if all_failed:
        log.info(f"失败: {', '.join(all_failed)}")
    log.info(f"文件位置: {DOWNLOAD_DIR}")
    log.info("=" * 60)

    summary = {
        "total": len(BOOKS),
        "success": success_count,
        "fail": fail_count,
        "failed_books": all_failed,
        "download_dir": str(DOWNLOAD_DIR),
    }
    (DOWNLOAD_DIR / "download_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
