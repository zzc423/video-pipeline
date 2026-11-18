# -*- coding: utf-8 -*-
"""给「造物实录」拉一批 Pixabay 实拍素材（视频优先）
产物：opc-remotion-studio/public/assets/broll/pixabay-<slug>-<id>.mp4
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

KEY = os.environ.get("PIXABAY_KEY", "")  # 免费申请：https://pixabay.com/api/docs/
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
OUT = Path(r"E:\Agent\OPC\opc-remotion-studio\public\assets\broll")

# (slug, 英文查询, 用途)
QUERIES = [
    ("caution",    "caution tape barrier",     "封锁/警示"),
    ("hands-lap",  "hands typing laptop",      "键盘"),
    ("unplug",     "network cable unplug",     "断线"),
    ("scaffold",   "construction scaffolding", "重建"),
    ("night-win",  "person window night",      "深夜"),
    ("notify",     "notification screen closeup", "消息"),
    ("clinic",     "modern clinic interior",   "医疗场景"),
    ("charts",     "financial charts screen",  "数据"),
    ("assembly",   "assembly line workers",    "流水线"),
    ("crowd",      "crowded queue people",      "人多"),
    ("control",    "control room monitors",    "控制室"),
    ("empty-desk", "empty office desk night",  "空工位"),
]

BANNED = ("coca", "pepsi", "nike", "adidas", "starbucks", "apple", "google")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with OPENER.open(req, timeout=30) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    added = []
    for slug, q, why in QUERIES:
        if any(p.name.startswith(f"pixabay-{slug}-") for p in OUT.iterdir() if p.is_file()):
            print(f"[跳过] {slug} 已有")
            continue
        url = ("https://pixabay.com/api/videos/?key=" + KEY
               + "&q=" + urllib.parse.quote(q) + "&per_page=3&safesearch=true")
        try:
            data = json.loads(get(url).decode("utf-8"))
        except Exception as e:
            print(f"[失败] {slug}: {str(e)[:80]}")
            continue

        for hit in data.get("hits", [])[:2]:
            tags = " ".join(hit.get("tags", "")).lower()
            if any(b in tags for b in BANNED):
                continue
            v = hit.get("videos", {})
            pick = v.get("medium") or v.get("small") or v.get("tiny")
            if not pick:
                continue
            src = pick.get("url")
            if not src:
                continue
            dst = OUT / f"pixabay-{slug}-{hit['id']}.mp4"
            try:
                raw = get(src)
            except Exception as e:
                print(f"  下载失败 {slug}: {str(e)[:60]}")
                continue
            if len(raw) < 200_000:
                continue
            dst.write_bytes(raw)
            added.append((slug, why, dst.name, len(raw) // 1024, f"{pick.get('width')}x{pick.get('height')}"))
            print(f"[+ ] {slug:11s} {why:6s} {len(raw)//1024:5d}KB {pick.get('width')}x{pick.get('height')}")
            break
        time.sleep(1.5)  # Pixabay 限速

    print(f"\n新增 {len(added)} 条")
    (OUT.parent.parent.parent / "tmp" / "review" / "stock-added.json").write_text(
        json.dumps(added, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
