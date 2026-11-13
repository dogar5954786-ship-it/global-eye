#!/usr/bin/env python3
"""Run by GitHub Actions when a photo is uploaded to inbox/<slug>/.

For every pending story that now has a photo:
  1. build the picture  -> posts/<slug>.jpg
  2. mark the story in pending.json as "ready" (with the picture path)
The hourly Claude bot then posts "ready" stories to Facebook.
"""
import datetime, html, json, os, subprocess, sys
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = "https://raw.githubusercontent.com/dogar5954786-ship-it/global-eye/main/"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
PKT = datetime.timezone(datetime.timedelta(hours=5))


def load(name, default):
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def save(name, data):
    with open(os.path.join(ROOT, name), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def photo_for(slug):
    d = os.path.join(ROOT, "inbox", slug)
    if not os.path.isdir(d):
        return None
    files = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(IMG_EXT)]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def credit_for(path):
    """Use the upload commit message as photo credit, unless it is GitHub's default text."""
    try:
        msg = subprocess.run(["git", "log", "-1", "--format=%s", "--", path], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""
    if not msg or msg.lower().startswith(("add files via upload", "create ", "upload ", "add ")):
        return ""
    return msg[:40]


def write_feed(items):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0">', "<channel>",
           "<title>Global Eye - ready posts</title>",
           "<link>https://github.com/dogar5954786-ship-it/global-eye</link>",
           "<description>Posts ready for the Global Eye Facebook page</description>"]
    for it in items[-30:][::-1]:
        out += ["<item>",
                f"<title>{html.escape(it['title'])}</title>",
                f"<link>{it['image']}</link>",
                f"<guid isPermaLink=\"false\">{it['guid']}</guid>",
                f"<pubDate>{it['pubDate']}</pubDate>",
                f"<description><![CDATA[{it['caption']}]]></description>",
                f"<enclosure url=\"{it['image']}\" type=\"image/jpeg\" length=\"{it.get('length', 0)}\"/>",
                "</item>"]
    out += ["</channel>", "</rss>"]
    with open(os.path.join(ROOT, "feed.xml"), "w") as f:
        f.write("\n".join(out) + "\n")


def main():
    pending = load("pending.json", [])
    posted = load("posted.json", [])
    feed = load("feed_items.json", [])
    keep, done = [], 0
    for e in pending:
        if e.get("status") == "ready":
            keep.append(e)
            continue
        ph = photo_for(e["slug"])
        if not ph:
            keep.append(e)
            continue
        out = os.path.join("posts", e["slug"] + ".jpg")
        cmd = [sys.executable, os.path.join(ROOT, "render_post.py"), "--style", "photo",
               "--category", e.get("category", "world"), "--headline", e["headline"],
               "--photo", ph, "--focus", str(e.get("focus", 0.3)), "--out", os.path.join(ROOT, out)]
        if e.get("breaking"):
            cmd.append("--breaking")
        cr = credit_for(ph)
        if cr:
            cmd += ["--credit", cr]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            print("render failed for", e["slug"], r.stderr)
            keep.append(e)
            continue
        now = datetime.datetime.now(PKT)
        e.update({"status": "ready", "image": out, "image_url": RAW + out,
                  "rendered": now.strftime("%Y-%m-%d %H:%M PKT")})
        keep.append(e)
        done += 1
        print("ready:", e["slug"])
    if done:
        save("pending.json", keep)
    print("done:", done)


if __name__ == "__main__":
    main()
