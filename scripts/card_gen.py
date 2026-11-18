# -*- coding: utf-8 -*-
"""图形卡生成器 v1（2026-11-17）

把视觉规范落成可批量出图的工具：JSON → 1920×1080 PNG。
产出的 PNG 直接当素材喂 MPT，不改 MPT 一行代码。

用法：
  python card_gen.py <cards.json> [--out <目录>]

cards.json 是一个数组，每项是一张卡：
  {"type":"cover",  "kicker":"[ 造物实录 · 001 ]", "title":"...<br><em>...</em>...",
                    "sub":"...", "meta":["22:14 时长","3200+ 次提交"], "no":"01"}
  {"type":"chapter","step":"[ STEP 02 ]", "title":"...", "sub":"...", "no":"02 / 06", "bar":52}
  {"type":"stats",  "title":"...", "items":[{"num":"3200","unit":"次提交","label":"..."}], "bar":76}
  {"type":"quote",  "text":"...<em>...</em>...", "by":"— 2026 年 8 月", "no":"06", "bar":84}
  {"type":"cmp",    "title":"...", "left":{"t":"2026-07","v":"227"}, "right":{"t":"2026-08","v":"33"}, "bar":92}
  {"type":"end",    "title":"...", "chips":["<b>评论区</b> 置顶有文档"], "no":"08", "bar":100}

依赖：系统 Edge（headless 截图），无需额外安装。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
:root{--bg:#0B0E14;--card:#161B26;--fg:#F5F7FA;--dim:#8A93A6;
      --cyan:#22D3EE;--violet:#A78BFA;--red:#F87171;
      --mono:"JetBrains Mono","Cascadia Mono",Consolas,monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1920px;height:1080px;overflow:hidden;color:var(--fg);
     font-family:"Source Han Sans SC","Noto Sans SC","Microsoft YaHei",sans-serif;
     background:radial-gradient(1200px 700px at 20% 0%,#1a2233 0%,var(--bg) 60%)}
.pad{position:absolute;inset:0;padding:96px 120px;display:flex;flex-direction:column}
.kicker{font-family:var(--mono);font-size:34px;color:var(--cyan);letter-spacing:.14em}
.foot{position:absolute;left:120px;right:120px;bottom:64px;display:flex;
      justify-content:space-between;font-family:var(--mono);font-size:26px;color:var(--dim)}
.bar{position:absolute;left:0;bottom:0;height:6px;background:var(--cyan)}
.cover h2{font-size:104px;line-height:1.06;font-weight:900;letter-spacing:-.02em;margin-top:40px}
.cover h2 em{font-style:normal;color:var(--cyan)}
.cover p.sub{font-size:44px;color:var(--dim);margin-top:44px;line-height:1.5;max-width:1280px}
.cover .meta{display:flex;gap:56px;margin-top:auto;margin-bottom:72px;font-family:var(--mono);font-size:30px;color:var(--dim)}
.cover .meta b{color:var(--fg);font-weight:600}
.chapter{justify-content:center}
.chapter .step{font-family:var(--mono);font-size:44px;color:var(--violet);letter-spacing:.2em}
.chapter h2{font-size:112px;font-weight:900;line-height:1.08;margin-top:32px}
.chapter .sub{font-size:40px;color:var(--dim);margin-top:36px}
.stats{justify-content:center}
.stats .row{display:flex;gap:96px;margin-top:56px}
.stats .item{flex:1}
.stats .num{font-family:var(--mono);font-size:140px;font-weight:700;line-height:1;
            color:var(--cyan);letter-spacing:-.03em;white-space:nowrap}
.stats .num small{font-size:44px;color:var(--dim);margin-left:14px;font-weight:400;
                  white-space:nowrap;display:inline-block;vertical-align:baseline}
.stats .lab{font-size:34px;color:var(--dim);margin-top:22px}
.stats h2{font-size:76px;font-weight:900;line-height:1.15}
.quote{align-items:center;justify-content:center;text-align:center}
.quote .mark{font-family:var(--mono);font-size:120px;color:#263044;line-height:.6}
.quote blockquote{font-size:104px;font-weight:900;line-height:1.18;margin:36px 0}
.quote blockquote em{font-style:normal;color:var(--red)}
.quote .by{font-family:var(--mono);font-size:30px;color:var(--dim)}
.cmp{justify-content:center}
.cmp .cols{display:grid;grid-template-columns:1fr 120px 1fr;gap:40px;align-items:center;margin-top:48px}
.cmp .box{background:var(--card);border:1px solid #263044;border-radius:16px;padding:56px}
.cmp .box.now{border-color:#3a2a2a}
.cmp .box .t{font-family:var(--mono);font-size:28px;color:var(--dim)}
.cmp .box .v{font-family:var(--mono);font-size:150px;font-weight:700;line-height:1.1;margin-top:18px}
.cmp .box.now .v{color:var(--red)}
.cmp .box.peak .v{color:var(--cyan)}
.cmp .arrow{font-size:80px;color:var(--dim);text-align:center}
.cmp h2{font-size:76px;font-weight:900}
.end{align-items:center;justify-content:center;text-align:center}
.end h2{font-size:88px;font-weight:900;line-height:1.2}
.end h2 em{font-style:normal;color:var(--cyan)}
.end .cta{display:flex;gap:24px;margin-top:56px}
.end .chip{font-family:var(--mono);font-size:30px;border:1px solid #263044;
           border-radius:999px;padding:16px 36px;color:var(--dim)}
.end .chip b{color:var(--cyan)}
"""


def find_edge() -> str:
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("找不到 Edge，无法截图")


def render(card: dict) -> str:
    t = card.get("type", "chapter")
    no = card.get("no", "")
    bar = card.get("bar", 30)
    foot = f'<div class="foot"><span>造物实录</span><span>{no}</span></div>'
    footer = f'<div class="bar" style="width:{bar}%"></div>'

    if t == "cover":
        meta = "".join(f"<span>{m}</span>" for m in card.get("meta", []))
        body = (f'<div class="pad cover"><div class="kicker">{card.get("kicker","")}</div>'
                f'<h2>{card.get("title","")}</h2>'
                f'<p class="sub">{card.get("sub","")}</p>'
                f'<div class="meta">{meta}</div></div>')
    elif t == "chapter":
        body = (f'<div class="pad chapter"><div class="step">{card.get("step","")}</div>'
                f'<h2>{card.get("title","")}</h2>'
                f'<div class="sub">{card.get("sub","")}</div></div>')
    elif t == "stats":
        items = "".join(
            f'<div class="item"><div class="num">{i.get("num","")}'
            f'<small>{i.get("unit","")}</small></div>'
            f'<div class="lab">{i.get("label","")}</div></div>'
            for i in card.get("items", []))
        body = (f'<div class="pad stats"><h2>{card.get("title","")}</h2>'
                f'<div class="row">{items}</div></div>')
    elif t == "quote":
        body = (f'<div class="pad quote"><div class="mark">“</div>'
                f'<blockquote>{card.get("text","")}</blockquote>'
                f'<div class="by">{card.get("by","")}</div></div>')
    elif t == "cmp":
        l, r = card.get("left", {}), card.get("right", {})
        body = (f'<div class="pad cmp"><h2>{card.get("title","")}</h2>'
                f'<div class="cols">'
                f'<div class="box peak"><div class="t">{l.get("t","")}</div>'
                f'<div class="v">{l.get("v","")}</div></div><div class="arrow">→</div>'
                f'<div class="box now"><div class="t">{r.get("t","")}</div>'
                f'<div class="v">{r.get("v","")}</div></div></div></div>')
    elif t == "end":
        chips = "".join(f'<span class="chip">{c}</span>' for c in card.get("chips", []))
        body = (f'<div class="pad end"><h2>{card.get("title","")}</h2>'
                f'<div class="cta">{chips}</div></div>')
    else:
        raise SystemExit(f"未知卡型: {t}")

    return f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}{foot}{footer}</body></html>"


def shoot(edge: str, html: str, out_png: Path):
    out_png = Path(out_png).resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / "c.html"
        hp.write_text(html, encoding="utf-8")
        subprocess.run([edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=1920,1080",
                        f"--screenshot={str(out_png)}",
                        hp.as_uri()],
                       capture_output=True, timeout=120)
    if not out_png.exists():
        raise SystemExit(f"截图失败: {out_png}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    src = Path(sys.argv[1])
    cards = json.loads(src.read_text(encoding="utf-8"))
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else src.parent
    out.mkdir(parents=True, exist_ok=True)
    edge = find_edge()

    for i, card in enumerate(cards, 1):
        name = f"{i:02d}-{card.get('type','card')}.png"
        dst = out / name
        shoot(edge, render(card), dst)
        print(f"[{i}] {dst}  {dst.stat().st_size // 1024}KB")
    print(f"\n完成 {len(cards)} 张 → {out}")


if __name__ == "__main__":
    main()
