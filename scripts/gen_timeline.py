# -*- coding: utf-8 -*-
"""按配音时长生成高密度视频时间线

输入：durations.json（由 make_audio.py 生成，含每段时长）
输出：timeline.json（每段的帧数、素材、字幕）

用法：
    python scripts/gen_timeline.py

改 PLAN 列表来换内容。每项 = (visual, 高亮词)
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DUR = BASE / "example" / "durations.json"
OUT = BASE / "example" / "timeline.json"
FPS = 30


def V(name):
    """视频素材"""
    return {"kind": "video", "src": f"assets/broll/{name}", "motion": "kenburns_in", "dim": 0.22}


def P(name, motion="kenburns_in"):
    """图片素材（带 Ken Burns 动态）"""
    return {"kind": "image", "src": f"assets/photos/{name}", "motion": motion, "dim": 0.18}


def SH(src, frame="browser", focus="center", zoom=1.1, url=""):
    """截图素材（装进浏览器框/手机机身）"""
    d = dict(src=f"assets/screenshot/{src}", frame=frame, focus=focus, zoom=zoom)
    if url:
        d["url"] = url
    return {"kind": "screenshot", "screenshot": d}


def C(preset, head, sub="", kicker="", **kw):
    """整屏卡片（注意：每段 <2 秒时标题动画来不及，慎用）"""
    d = dict(preset=preset, kicker=kicker, head=head, sub=sub, foot="")
    d.update(kw)
    return {"kind": "card", "card": d}


# ── 示例：把 durations.json 的段依次配上素材 ──
# 换内容时只需要改这里。素材放 public/assets/{broll,photos,screenshot}/
PLAN = [
    (P("px-money-1935415.jpg"), []),
    (P("px-coin-2414.jpg", "kenburns_out"), []),
    (V("pixabay-server-345428.mp4"), []),
    (V("pixabay-hands-lap-10822.mp4"), []),
    (P("px-desk-night-2587598.jpg", "pan_right"), []),
    (V("pixabay-empty-desk-150883.mp4"), []),
    (V("pixabay-scaffold-214661.mp4"), []),
    (V("pixabay-server-345428.mp4"), []),
]

CHAP = [("开场", "s-01", "s-04"), ("正文", "s-05", "s-08")]


def main():
    durations = json.loads(DUR.read_text(encoding="utf-8"))
    if len(durations) != len(PLAN):
        raise SystemExit(f"段数不符：配音 {len(durations)} 段，PLAN {len(PLAN)} 段")

    segs = []
    for d, (visual, hl) in zip(durations, PLAN):
        cap = {"style": "subtitle", "text": d["text"]}
        if hl:
            cap["highlight"] = hl
        segs.append({
            "id": d["id"],
            "narration": d["text"],
            "frames": max(18, round(d["duration"] * FPS)),
            "transition": "cut",  # 高密度片一律硬切，fade 会叠层
            "visual": visual,
            "caption": cap,
        })

    timeline = {
        "slug": BASE.name,
        "title": "示例：一条高密度知识视频",
        "format": {"w": 1080, "h": 1920, "fps": FPS},
        "voice": {"id": "zh-CN-YunxiNeural", "speed": 1.15, "enabled": True},
        "chapters": [{"label": a, "from": b, "to": c} for a, b, c in CHAP],
        "segments": segs,
    }
    OUT.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(s["frames"] for s in segs) / FPS
    print(f"{len(segs)} 段 / {total:.1f}s / 平均 {total/len(segs):.2f}s 一段 → {OUT}")

    bad = []
    for s in segs:
        src = s["visual"].get("src")
        if src and not (BASE / "public" / src).exists():
            bad.append(src)
    if bad:
        print("⚠️ 素材缺失（请放到 public/assets/ 下）:")
        for b in bad[:8]:
            print("  ", b)


if __name__ == "__main__":
    main()
