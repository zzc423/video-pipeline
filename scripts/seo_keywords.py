# -*- coding: utf-8 -*-
"""关键词优化组件 v1（2026-11-17）

管道第 ⓪ 步的固定组件：从真实搜索建议里挖词，产出写稿用的词表。

数据源（都免登录、免 key）：
  - B站搜索建议 s.search.bilibili.com   ← 长视频主场，最贴合
  - 百度下拉   suggestion.baidu.com     ← 中文搜索意图最全

用法：
  python seo_keywords.py research AI做视频 一人公司 视频流水线
       → 输出候选池 + 写入 output/<日期>-keywords/keywords.json
  python seo_keywords.py pack <slug> --core <核心词> --script <script.md>
       → 生成标题候选 / 描述 / 标签，写 seo.json

选词规则（2026 平台口径）：
  1 核心词 + 3-5 长尾词 + 2 相关词；标题含 ≥3 个目标词
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(r"E:\Agent\OPC")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _get(url: str, timeout: int = 15, extra_headers=None) -> bytes:
    headers = {**UA, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def bili_suggest(term: str) -> list[str]:
    """B站搜索建议。返回按热度排序的联想词。"""
    url = ("https://s.search.bilibili.com/main/suggest?term="
           + urllib.parse.quote(term) + "&main_ver=v1")
    try:
        data = json.loads(_get(url).decode("utf-8"))
        return [t.get("value", "") for t in data.get("result", {}).get("tag", [])
                if t.get("value")]
    except Exception as e:
        print(f"  [B站] 失败: {e}", file=sys.stderr)
        return []


def douyin_suggest(term: str) -> list[str]:
    """抖音搜索建议。主阵地，免签名免登录。返回 content 列表（按平台排序）。"""
    url = ("https://www.douyin.com/aweme/v1/web/search/sug/?keyword="
           + urllib.parse.quote(term) + "&device_platform=webapp&aid=6383")
    try:
        data = json.loads(_get(url, extra_headers={"Referer": "https://www.douyin.com/"}).decode("utf-8"))
        out = []
        for item in data.get("sug_list", []):
            c = (item.get("content") or "").strip()
            if c:
                out.append(c)
        return out
    except Exception as e:
        print(f"  [抖音] 失败: {e}", file=sys.stderr)
        return []


def baidu_suggest(term: str) -> list[str]:
    """百度下拉。返回 JSONP → 正则抠出 s:["..."]。注意响应是 GBK。"""
    url = ("https://suggestion.baidu.com/su?wd="
           + urllib.parse.quote(term) + "&cb=x&encoding=utf-8")
    try:
        txt = _get(url).decode("gbk", errors="replace")
        m = re.search(r's:\s*\[(.*?)\]', txt, re.S)
        if not m:
            return []
        return [w.strip() for w in re.findall(r'"([^"]+)"', m.group(1)) if w.strip()]
    except Exception as e:
        print(f"  [百度] 失败: {e}", file=sys.stderr)
        return []


def research(seeds: list[str]) -> dict:
    """对每个种子词收集候选，输出结构化结果。"""
    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "seeds": {}}
    for s in seeds:
        dy = douyin_suggest(s)
        b = bili_suggest(s)
        d = baidu_suggest(s)
        out["seeds"][s] = {"douyin": dy, "bilibili": b, "baidu": d}
        print(f"\n【{s}】")
        if dy:
            print("  抖音:", " / ".join(dy[:8]))
        if b:
            print("  B站 :", " / ".join(b[:8]))
        if d:
            print("  百度:", " / ".join(d[:8]))
        time.sleep(0.5)  # 温和请求，别把接口打毛
    return out


def rank_pool(data: dict) -> list[tuple[str, float]]:
    """把候选词汇总打分：越靠前、被越多来源提到，分越高。"""
    score: dict[str, float] = {}
    for s, src in data["seeds"].items():
        # 权重：抖音 1.2（主阵地）> B站 1.0 > 百度 0.6
        for name, words, wt in (("douyin", src.get("douyin", []), 1.2),
                                ("bili", src.get("bilibili", []), 1.0),
                                ("baidu", src.get("baidu", []), 0.6)):
            for i, w in enumerate(words):
                score[w] = score.get(w, 0) + wt / (i + 1)
    return sorted(score.items(), key=lambda kv: -kv[1])


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        sys.exit(2)
    cmd = argv[0]

    if cmd == "research":
        seeds = argv[1:]
        if not seeds:
            print("用法: research <种子词...>")
            sys.exit(2)
        data = research(seeds)
        out_dir = BASE / "output" / f"{time.strftime('%Y-%m-%d')}-keywords"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "keywords.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        pool = rank_pool(data)
        print(f"\n=== 候选池 Top 20（按热度加权）===")
        for w, sc in pool[:20]:
            print(f"  {sc:5.2f}  {w}")
        print(f"\n[写入] {out_dir / 'keywords.json'}")
        return

    if cmd == "pack":
        # 用法：pack <slug> --core <核心词> [--script <script.md>]
        rest = argv[1:]
        if not rest:
            print("用法: pack <slug> --core <核心词> [--script <script.md>]")
            sys.exit(2)
        slug = rest[0]
        core = ""
        script_path = None
        for i, a in enumerate(rest):
            if a == "--core" and i + 1 < len(rest):
                core = rest[i + 1]
            if a == "--script" and i + 1 < len(rest):
                script_path = Path(rest[i + 1])

        # 读同日的 keywords.json（research 的产物）
        kw_files = sorted((BASE / "output").glob("*-keywords/keywords.json"))
        if not kw_files:
            print("先跑 research 产出词表")
            sys.exit(1)
        data = json.loads(kw_files[-1].read_text(encoding="utf-8"))

        # 只在「核心词自己那一组」里选，不跨种子词串味
        seed_key = next((k for k in data["seeds"]
                         if k.lower() == core.lower()), None)
        if not seed_key:
            print(f"keywords.json 里没有种子词「{core}」，先 research 它")
            sys.exit(1)
        src = data["seeds"][seed_key]
        seen, cand = set(), []
        for key in ("douyin", "bilibili", "baidu"):   # 抖音优先
            for w in src.get(key, []):
                if w.lower() not in seen:
                    seen.add(w.lower())
                    cand.append(w)

        # 偏题词根：命中就打标，不直接删（可能仍有价值，人来判断）
        OFF = ["流水线", "工厂", "招聘", "打工", "连带责任", "注册",
               "优缺点", "什么意思", "实拍", "加工厂"]
        cl = core.lower()
        # 长尾 = 含核心词的扩展词（搜索时能命中核心词）；相关 = 不含核心词的同域词
        longs = [w for w in cand if cl in w.lower() and w.lower() != cl][:5]
        related = [w for w in cand if cl not in w.lower()][:2]

        def mark(w: str) -> str:
            return "  ⚠️偏题" if any(o in w for o in OFF) else ""

        # 标题候选：模板 × 真实数字（数字留给正文填）
        tpl = [
            f"{core}｜一个人做出 {{{{N}}}} 条，我把方法摊开",
            f"我用 {core} 跑了 {{{{N}}}} 天，踩了 {{{{M}}}} 个坑",
            f"{core}怎么做？先别买课，看这套真实流程",
            f"不靠剪辑，{core}从 {{{{A}}}} 到 {{{{B}}}} 全记录",
            f"{longs[0] if longs else core}，一次讲透",
        ]
        desc = (
            f"{core}到底怎么做？这条视频讲的是真实跑通的流程，不是理论。\n"
            f"下面是全过程的步骤、卡点和真实数据。\n\n"
            + ("章节：\n" if not script_path else "章节：见视频分章\n")
        )
        tags = [core] + longs[:4] + related[:2]

        seo = {
            "slug": slug,
            "core": core,
            "long_tail": longs,
            "related": related,
            "titles": tpl,
            "description": desc,
            "tags": tags,
            "generated": time.strftime("%Y-%m-%d %H:%M"),
        }
        out_dir = BASE / "output" / f"{time.strftime('%Y-%m-%d')}-{slug}"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "seo.json").write_text(
            json.dumps(seo, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"\n核心词：{core}")
        print("长尾  ：", " / ".join(f"{w}{mark(w)}" for w in longs) or "（无，需补 research）")
        print("相关  ：", " / ".join(f"{w}{mark(w)}" for w in related) or "（无）")
        print("\n标题候选：")
        for i, t in enumerate(tpl, 1):
            print(f"  {i}. {t}")
        print("\n标签：", " ".join(tags))
        bad = [w for w in tags if any(o in w for o in OFF)]
        if bad:
            print("⚠️ 标签里含偏题词，建议删:", " / ".join(bad))
        print(f"\n[写入] {out_dir / 'seo.json'}")
        return

    print(__doc__)
    sys.exit(2)


if __name__ == "__main__":
    main()
