# -*- coding: utf-8 -*-
"""抓一批 Pixabay 图片，落 public/assets/photos/，带亮度体检"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

KEY = os.environ.get("PIXABAY_KEY", "")  # 免费申请：https://pixabay.com/api/docs/
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
OUT = Path(r"E:\Agent\OPC\opc-remotion-studio\public\assets\photos")
BANNED = ("coca", "pepsi", "nike", "adidas", "starbucks", "apple", "google")

QUERIES = [
    ("money", "chinese yuan banknote", "一毛钱"),
    ("coin", "coins macro", "成本"),
    ("terminal", "terminal screen code", "终端"),
    ("screen-code", "programmer screen closeup", "代码屏"),
    ("server-rack", "server rack lights", "服务器"),
    ("ai-brain", "artificial intelligence abstract", "AI"),
    ("factory", "factory assembly line", "生产线"),
    ("conveyor", "conveyor belt", "流水线"),
    ("clock", "clock macro time", "时间"),
    ("document", "documents stack paper", "文档"),
    ("error", "red error screen", "报错"),
    ("keyboard-macro", "keyboard macro closeup", "键盘"),
    ("desk-night", "desk lamp night work", "深夜"),
    ("city-roof", "city rooftop skyline", "城市"),
    ("network", "network cables server", "网络"),
    ("cloud", "cloud computing abstract", "云"),
    ("robot-arm", "robot arm industry", "自动化"),
    ("blueprint-plan", "technical blueprint plan", "蓝图"),
    ("alarm", "warning siren red", "警报"),
    ("data-center", "data center corridor", "数据中心"),
    ("notebook", "notebook pen writing", "笔记"),
    ("globe-net", "global network connections", "网络"),
    ("light-bulb", "idea light bulb", "想法"),
    ("ladder", "ladder steps up", "步骤"),
]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with OPENER.open(req, timeout=30) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    added = []
    for slug, q, why in QUERIES:
        if any(p.name.startswith(f"px-{slug}-") for p in OUT.iterdir() if p.is_file()):
            continue
        url = ("https://pixabay.com/api/?key=" + KEY + "&q=" + urllib.parse.quote(q)
               + "&image_type=photo&orientation=vertical&per_page=6&safesearch=true")
        try:
            data = json.loads(get(url).decode("utf-8"))
        except Exception as e:
            print(f"[失败] {slug}: {str(e)[:70]}")
            continue
        for hit in data.get("hits", [])[:4]:
            tags = " ".join(hit.get("tags", "")).lower()
            if any(b in tags for b in BANNED):
                continue
            src = hit.get("largeImageURL") or hit.get("webformatURL")
            w, h = hit.get("imageWidth"), hit.get("imageHeight")
            if not src or not w or w < 800:
                continue
            dst = OUT / f"px-{slug}-{hit['id']}.jpg"
            try:
                raw = get(src)
            except Exception:
                continue
            if len(raw) < 60_000:
                continue
            dst.write_bytes(raw)
            added.append(dict(slug=slug, why=why, file=dst.name, w=w, h=h, kb=len(raw) // 1024))
            print(f"[+ ] {slug:14s} {why:6s} {w}x{h} {len(raw)//1024}KB")
            break
    print(f"\n新增 {len(added)} 张")


if __name__ == "__main__":
    main()
