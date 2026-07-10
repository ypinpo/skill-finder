#!/usr/bin/env python3
"""
4K 成人视频下载器 — 基于 yt-dlp + aria2c 双引擎
================================================
支持: Eporner / SpankBang / XVideos / PornHub / XHamster
      + 磁力链接 (magnet) 降级模式

用法:
  # 单链接
  python 4k_downloader.py "https://www.eporner.com/video-xxx/"

  # 批量
  python 4k_downloader.py urls.txt

  # 搜索
  python 4k_downloader.py --search "xvideos:关键词" --max 5

  # 磁力链接
  python 4k_downloader.py --magnet "magnet:?xt=urn:btih:XXX"

  # 自定义输出目录 + 代理
  python 4k_downloader.py --output-dir "D:\\Videos" --proxy socks5://127.0.0.1:10808 "https://..."

依赖: yt-dlp, aria2c (磁力模式), Python 3.8+
"""

import argparse
import logging
import os
import random
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = os.path.join(str(Path.home()), "Downloads", "4K_Videos")
COMMON_PROXY_PORTS = [
    ("http://127.0.0.1:7890", "Clash / Clash Verge"),
    ("http://127.0.0.1:7891", "Clash Verge (备用)"),
    ("socks5://127.0.0.1:10808", "v2rayN"),
    ("socks5://127.0.0.1:1080", "Shadowsocks / 通用"),
]

# 支持的站点搜索前缀
SITE_SEARCH_MAP = {
    "eporner": "Eporner",
    "spankbang": "SpankBang",
    "xvideos": "XVideos",
    "pornhub": "PornHub",
    "xhamster": "XHamster",
}

# ── 日志 ──────────────────────────────────────────────
class ColoredFormatter(logging.Formatter):
    """彩色控制台输出"""
    COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = ColoredFormatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [h]


log = logging.getLogger("4k_dl")

# ── 代理探测 ──────────────────────────────────────────
def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """检测端口是否开放"""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def auto_detect_proxy() -> str | None:
    """自动探测本机代理端口"""
    for proxy_url, name in COMMON_PROXY_PORTS:
        # 解析 host:port
        # socks5://127.0.0.1:10808 → host=127.0.0.1, port=10808
        rest = proxy_url.split("://", 1)[1]
        host, port_str = rest.rsplit(":", 1)
        port = int(port_str)
        if check_port(host, port):
            log.info(f"🔍 检测到代理: {name} → {proxy_url}")
            return proxy_url
    return None


def resolve_proxy(proxy_arg: str | None) -> str | None:
    """
    解析代理，优先级:
    1. --proxy 命令行参数
    2. HTTP_PROXY / HTTPS_PROXY / ALL_PROXY 环境变量
    3. 自动探测常见端口
    """
    if proxy_arg:
        return proxy_arg

    for env_var in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"):
        val = os.environ.get(env_var)
        if val:
            log.info(f"📡 使用环境变量 {env_var}={val}")
            return val

    detected = auto_detect_proxy()
    if detected:
        return detected

    log.warning("⚠️  未检测到代理！国外站点可能无法访问。")
    log.warning("   请指定 --proxy 或设置 HTTPS_PROXY 环境变量。")
    log.warning("   推荐安装 Clash Verge Rev: https://github.com/clash-verge-rev/clash-verge-rev/releases")
    return None


# ── 用户代理 ──────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]


def random_ua() -> str:
    return random.choice(USER_AGENTS)


# ── 文件名清理 ────────────────────────────────────────
def sanitize_filename(name: str) -> str:
    """移除文件名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()[:200]


# ── 磁力下载 (aria2c) ─────────────────────────────────
def download_magnet(magnet: str, output_dir: str) -> bool:
    """使用 aria2c 下载磁力链接"""
    aria2 = find_aria2()
    if not aria2:
        log.error("❌ aria2c 未找到！请安装: winget install aria2")
        return False

    log.info(f"🧲 磁力下载: {magnet[:60]}...")
    log.info(f"📁 输出: {output_dir}")

    cmd = [
        aria2,
        "--dir", output_dir,
        "--seed-time=0",              # 下载完不做种
        "--max-connection-per-server=16",
        "--split=16",
        "--min-split-size=1M",
        "--console-log-level=warn",
        "--summary-interval=30",
        magnet,
    ]

    try:
        subprocess.run(cmd, check=True)
        log.info("✅ 磁力下载完成！")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"❌ aria2c 下载失败: {e}")
        return False
    except KeyboardInterrupt:
        log.warning("⚠️  用户中断，aria2c 支持断点续传，重新运行可恢复。")
        return False


def find_aria2() -> str | None:
    """查找 aria2c 可执行文件"""
    import shutil
    aria2 = shutil.which("aria2c")
    if aria2:
        return aria2

    # Windows 常见路径
    for p in [
        r"C:\Program Files\aria2\aria2c.exe",
        r"C:\Program Files (x86)\aria2\aria2c.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\aria2c.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\*\aria2c.exe"),
    ]:
        expanded = Path(p)
        if expanded.exists():
            return str(expanded)
        # 处理通配符
        parent = expanded.parent
        if "*" in str(parent):
            import glob as g
            matches = g.glob(str(parent))
            for m in matches:
                candidate = Path(m) / expanded.name
                if candidate.exists():
                    return str(candidate)
    return None


# ── yt-dlp 下载 ───────────────────────────────────────
def build_ytdlp_args(url: str, output_dir: str, proxy: str | None,
                     limit_rate: str, concurrent: int,
                     sleep_req: float, sleep_int: float,
                     retries: int, no_4k: bool) -> list:
    """构建 yt-dlp 命令行参数"""
    height_limit = "1080" if no_4k else "2160"
    fmt = f"bestvideo[height<={height_limit}]+bestaudio/best[height<={height_limit}]/best"

    args = [
        sys.executable, "-m", "yt_dlp",
        "--format", fmt,
        "--merge-output-format", "mp4",
        "--output", os.path.join(output_dir, "%(title).200s [%(id)s].%(ext)s"),
        "--concurrent-fragments", str(concurrent),
        "--limit-rate", limit_rate,
        "--sleep-requests", str(sleep_req),
        "--sleep-interval", str(sleep_int),
        "--sleep-subtitles", "3",
        "--retries", str(retries),
        "--fragment-retries", str(retries),
        "--extractor-retries", str(retries),
        "--user-agent", random_ua(),
        "--no-check-certificates",
        "--no-warnings",
        "--progress",
        "--newline",
    ]

    if proxy:
        args.extend(["--proxy", proxy])

    args.append(url)
    return args


def download_ytdlp(url: str, output_dir: str, proxy: str | None,
                   limit_rate: str = "10M", concurrent: int = 3,
                   sleep_req: float = 3.0, sleep_int: float = 5.0,
                   retries: int = 5, no_4k: bool = False) -> bool:
    """使用 yt-dlp 下载"""
    log.info(f"🎬 下载: {url}")
    log.info(f"📁 输出: {output_dir}")
    log.info(f"🎯 分辨率: {'≤1080p' if no_4k else '4K 优先 (≤2160p)'}")

    cmd = build_ytdlp_args(url, output_dir, proxy, limit_rate, concurrent,
                           sleep_req, sleep_int, retries, no_4k)

    log.debug(f"🔧 命令: {' '.join(cmd)}")

    try:
        proc = subprocess.run(cmd)
        if proc.returncode == 0:
            log.info("✅ 下载完成！")
            return True
        else:
            log.error(f"❌ yt-dlp 退出码: {proc.returncode}")
            return False
    except KeyboardInterrupt:
        log.warning("⚠️  用户中断。重新运行可断点续传。")
        return False
    except FileNotFoundError:
        log.error("❌ yt-dlp 未安装！请运行: pip install yt-dlp")
        return False


# ── 搜索模式 ──────────────────────────────────────────
def search_and_download(query: str, output_dir: str, proxy: str | None,
                        max_results: int = 5, **kwargs) -> int:
    """搜索并下载"""
    # 格式: "site:keyword" 或直接 "keyword"
    # yt-dlp 搜索: ytsearchN:keyword 或 site:keyword
    parts = query.split(":", 1)
    if len(parts) == 2 and parts[0].lower() in SITE_SEARCH_MAP:
        site = parts[0].lower()
        keyword = parts[1]
        search_query = f"{site}:{keyword}"
    else:
        search_query = query

    ytdlp_search = f"ytsearch{max_results}:{search_query}"

    log.info(f"🔍 搜索: {search_query} (最多 {max_results} 个)")
    log.info("⚠️  搜索模式可能因站点限制而失败，建议直接提供链接。")

    return download_ytdlp(ytdlp_search, output_dir, proxy, **kwargs)


# ── 批量下载 ──────────────────────────────────────────
def download_batch(filepath: str, output_dir: str, proxy: str | None,
                   **kwargs) -> tuple[int, int]:
    """从文件批量下载，每行一个链接，# 开头为注释"""
    if not os.path.isfile(filepath):
        log.error(f"❌ 文件不存在: {filepath}")
        return 0, 0

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    urls = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    if not urls:
        log.warning("⚠️  文件中没有有效的 URL。")
        return 0, 0

    log.info(f"📋 批量下载 {len(urls)} 个视频")
    success = 0
    fail = 0

    for i, url in enumerate(urls, 1):
        log.info(f"\n{'='*50}")
        log.info(f"[{i}/{len(urls)}] 处理中...")
        log.info(f"{'='*50}")

        # 检测是否是磁力链接
        if url.startswith("magnet:?xt=urn:btih:"):
            ok = download_magnet(url, output_dir)
        else:
            ok = download_ytdlp(url, output_dir, proxy, **kwargs)

        if ok:
            success += 1
        else:
            fail += 1

        # 请求间隔（避免 IP 被封）
        if i < len(urls):
            delay = random.uniform(5, 15)
            log.info(f"⏳ 等待 {delay:.1f}s 再处理下一条...")
            time.sleep(delay)

    return success, fail


# ── 命令行参数 ────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="4K 成人视频下载器 — yt-dlp + aria2c 双引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "https://www.eporner.com/video-xxx/"
  %(prog)s --proxy socks5://127.0.0.1:10808 "https://..."
  %(prog)s --search "xvideos:关键词" --max 5
  %(prog)s --magnet "magnet:?xt=urn:btih:XXX"
  %(prog)s urls.txt --output-dir "D:\\Videos"
        """,
    )
    p.add_argument(
        "input",
        nargs="?",
        help="视频 URL 或 urls.txt 文件路径",
    )
    p.add_argument(
        "--search", "-s",
        help="搜索关键词 (格式: site:keyword 如 xvideos:xxx)",
    )
    p.add_argument(
        "--magnet", "-m",
        help="磁力链接 (magnet:?xt=urn:btih:...)",
    )
    p.add_argument(
        "--max", type=int, default=5,
        help="搜索模式最大结果数 (默认 5)",
    )
    p.add_argument(
        "--output-dir", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})",
    )
    p.add_argument(
        "--proxy", "-p",
        help="代理地址 (如 socks5://127.0.0.1:10808 或 http://127.0.0.1:7890)",
    )
    p.add_argument(
        "--limit-rate", "-r",
        default="10M",
        help="下载限速 (默认 10M，如 5M / 20M)",
    )
    p.add_argument(
        "--concurrent", "-c", type=int, default=3,
        help="并发分片数 (默认 3)",
    )
    p.add_argument(
        "--sleep-requests", type=float, default=3.0,
        help="请求间隔秒数 (默认 3.0)",
    )
    p.add_argument(
        "--sleep-interval", type=float, default=5.0,
        help="下载间隔秒数 (默认 5.0)",
    )
    p.add_argument(
        "--retries", type=int, default=5,
        help="失败重试次数 (默认 5)",
    )
    p.add_argument(
        "--no-4k", action="store_true",
        help="禁用 4K，只下载 ≤1080p",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="详细日志",
    )
    return p.parse_args()


# ── 主流程 ────────────────────────────────────────────
def main():
    args = parse_args()
    setup_logging(args.verbose)

    # 打印横幅
    log.info("=" * 55)
    log.info("  4K 成人视频下载器  |  yt-dlp + aria2c 双引擎")
    log.info("=" * 55)

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 解析代理
    proxy = resolve_proxy(args.proxy)

    # 通用参数
    dl_kwargs = {
        "output_dir": args.output_dir,
        "proxy": proxy,
        "limit_rate": args.limit_rate,
        "concurrent": args.concurrent,
        "sleep_req": args.sleep_requests,
        "sleep_int": args.sleep_interval,
        "retries": args.retries,
        "no_4k": args.no_4k,
    }

    # ── 磁力模式 ──
    if args.magnet:
        ok = download_magnet(args.magnet, args.output_dir)
        sys.exit(0 if ok else 1)

    # ── 搜索模式 ──
    if args.search:
        ok = search_and_download(args.search, max_results=args.max, **dl_kwargs)
        sys.exit(0 if ok else 1)

    # ── 无输入 ──
    if not args.input:
        log.error("❌ 请提供 URL、urls.txt 文件、--search 或 --magnet 参数。")
        log.info("   用法: python 4k_downloader.py --help")
        sys.exit(1)

    # ── 批量模式 (文件) ──
    if args.input.endswith(".txt") or os.path.isfile(args.input):
        success, fail = download_batch(args.input, **dl_kwargs)
        log.info(f"\n📊 批量完成: ✅ {success} / ❌ {fail}")
        sys.exit(0 if fail == 0 else 1)

    # ── 单链接模式 ──
    if args.input.startswith("magnet:?xt=urn:btih:"):
        ok = download_magnet(args.input, args.output_dir)
    else:
        ok = download_ytdlp(args.input, **dl_kwargs)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    # SIGINT 友好退出
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    main()
