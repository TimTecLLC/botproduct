#!/usr/bin/env python3
"""Build WordPress migration artifacts from timtec.net."""

from __future__ import annotations

import csv
import html
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

BASE = "https://www.timtec.net"
OUTPUT = Path(__file__).resolve().parents[1] / "output"
USER_AGENT = "TimTecMigrationBot/1.0 (+https://www.timtec.net)"


def fetch(url: str) -> tuple[int, str, str]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, resp.geturl(), body


def normalize_path(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in {"www.timtec.net", "timtec.net"}:
        return None
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return path


def extract_title(page_html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", page_html, re.I | re.S)
    if not m:
        return "Untitled"
    title = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
    return title.split("|")[0].strip() or "Untitled"


def extract_main_content(page_html: str) -> str:
    for pattern in (
        r'<div[^>]+class="[^"]*item-page[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        r'<div[^>]+class="[^"]*rt-article[^"]*"[^>]*>(.*?)</div>\s*</div>',
        r"<article[^>]*>(.*?)</article>",
    ):
        m = re.search(pattern, page_html, re.I | re.S)
        if m:
            return cleanup_html(m.group(1))
    body = re.search(r"<body[^>]*>(.*)</body>", page_html, re.I | re.S)
    return cleanup_html(body.group(1) if body else page_html)


def cleanup_html(fragment: str) -> str:
    fragment = re.sub(r"<script[\s\S]*?</script>", "", fragment, flags=re.I)
    fragment = re.sub(r"<style[\s\S]*?</style>", "", fragment, flags=re.I)
    fragment = re.sub(r"\s+", " ", fragment)
    return fragment.strip()


def wordpress_slug(path: str) -> str:
    if path == "/":
        return "home"
    slug = path.strip("/")
    if slug.endswith(".html"):
        slug = slug[:-5]
    return slug.lower()


def infer_post_type(path: str, title: str, content: str) -> str:
    lower = f"{path} {title}".lower()
    if any(k in lower for k in ("news", "blog", "announce", "celebrating", "may 2019")):
        return "post"
    if path.startswith("/category/") or path.startswith("/faqs/"):
        return "category"
    return "page"


def crawl_site(limit: int = 250) -> list[dict]:
    queue: deque[str] = deque([BASE + "/"])
    seen: set[str] = set()
    pages: list[dict] = []

    while queue and len(pages) < limit:
        url = queue.popleft()
        path = normalize_path(url)
        if not path or path in seen:
            continue
        seen.add(path)

        try:
            status, final_url, body = fetch(url if url.startswith("http") else urljoin(BASE, url))
        except Exception as exc:
            print(f"skip {url}: {exc}", file=sys.stderr)
            continue

        if status >= 400:
            continue

        final_path = normalize_path(final_url) or path
        title = extract_title(body)
        content = extract_main_content(body)
        post_type = infer_post_type(final_path, title, content)

        pages.append(
            {
                "source_url": final_url,
                "source_path": final_path,
                "title": title,
                "content": content,
                "post_type": post_type,
                "wp_slug": wordpress_slug(final_path),
            }
        )

        for href in re.findall(r'href="([^"]+)"', body, flags=re.I):
            if href.startswith(("mailto:", "javascript:", "#")):
                continue
            full = urljoin(final_url, href)
            p = normalize_path(full)
            if not p:
                continue
            if p.endswith(".html") or p == "/" or p.startswith("/category/") or p.startswith("/faqs/"):
                if p not in seen:
                    queue.append(full)
        time.sleep(0.15)

    return pages


def write_inventory(pages: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["source_path", "source_url", "title", "post_type", "wp_slug", "content_length"],
        )
        writer.writeheader()
        for page in pages:
            writer.writerow(
                {
                    **{k: page[k] for k in ("source_path", "source_url", "title", "post_type", "wp_slug")},
                    "content_length": len(page["content"]),
                }
            )


def write_redirects(pages: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source", "target", "http_code", "notes"])
        for page in pages:
            source = page["source_path"]
            target = "/" if page["wp_slug"] == "home" else f"/{page['wp_slug']}/"
            writer.writerow([source, target, 301, page["title"]])


def write_wxr(pages: list[dict], path: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:excerpt": "http://wordpress.org/export/1.2/excerpt/",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
            "xmlns:wfw": "http://wellformedweb.org/CommentAPI/",
            "xmlns:dc": "http://purl.org/dc/elements/1.1/",
            "xmlns:wp": "http://wordpress.org/export/1.2/",
        },
    )
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "TimTec"
    ET.SubElement(channel, "link").text = BASE
    ET.SubElement(channel, "description").text = "TimTec Joomla to WordPress migration export"
    ET.SubElement(channel, "pubDate").text = now
    ET.SubElement(channel, "language").text = "en-US"
    ET.SubElement(channel, "wp:wxr_version").text = "1.2"
    ET.SubElement(channel, "wp:base_site_url").text = BASE
    ET.SubElement(channel, "wp:base_blog_url").text = BASE

    post_id = 1
    for page in pages:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = page["title"]
        ET.SubElement(item, "link").text = page["source_url"]
        ET.SubElement(item, "pubDate").text = now
        ET.SubElement(item, "dc:creator").text = "timtec"
        guid = ET.SubElement(item, "guid", {"isPermaLink": "false"})
        guid.text = page["source_url"]
        ET.SubElement(item, "description")
        content = ET.SubElement(item, "content:encoded")
        content.text = page["content"]
        excerpt = ET.SubElement(item, "excerpt:encoded")
        excerpt.text = ""
        ET.SubElement(item, "wp:post_id").text = str(post_id)
        ET.SubElement(item, "wp:post_date").text = now
        ET.SubElement(item, "wp:post_date_gmt").text = now
        ET.SubElement(item, "wp:post_modified").text = now
        ET.SubElement(item, "wp:post_modified_gmt").text = now
        ET.SubElement(item, "wp:comment_status").text = "closed"
        ET.SubElement(item, "wp:ping_status").text = "closed"
        ET.SubElement(item, "wp:post_name").text = page["wp_slug"]
        ET.SubElement(item, "wp:status").text = "draft"
        ET.SubElement(item, "wp:post_parent").text = "0"
        ET.SubElement(item, "wp:menu_order").text = "0"
        ET.SubElement(item, "wp:post_type").text = page["post_type"] if page["post_type"] in {"post", "page"} else "page"
        ET.SubElement(item, "wp:post_password").text = ""
        ET.SubElement(item, "wp:is_sticky").text = "0"
        post_id += 1

    tree = ET.ElementTree(rss)
    ET.register_namespace("excerpt", "http://wordpress.org/export/1.2/excerpt/")
    ET.register_namespace("content", "http://purl.org/rss/1.0/modules/content/")
    ET.register_namespace("wfw", "http://wellformedweb.org/CommentAPI/")
    ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    ET.register_namespace("wp", "http://wordpress.org/export/1.2/")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pages = crawl_site()
    write_inventory(pages, OUTPUT / "content-inventory.csv")
    write_redirects(pages, OUTPUT / "redirects.csv")
    write_wxr(pages, OUTPUT / "timtec-wordpress-import.xml")
    print(f"Generated {len(pages)} records in {OUTPUT}")


if __name__ == "__main__":
    main()
