# -*- coding: utf-8 -*-
"""造物实录 · 这条视频成本一毛钱 · 54 段短配音（1.5-2.5 秒/段）"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]  # 仓库根
MPT = BASE / "vendor" / "mpt-env" / "Scripts" / "mpt.exe"
MPT_HOME = Path(r"E:\Agent\tmp\mpt-home")
VOICE = "zh-CN-YunxiNeural"
OUT = BASE / "opc-remotion-studio" / "public" / "audio" / "video-line-001"
DUR = BASE / "opc-remotion-studio" / "src" / "compositions" / "video-line-001" / "durations.json"

LINES = [
    # 开场：反常识连发
    "这条视频",
    "成本一毛钱",
    "从文案到成片",
    "我没打开过剪辑软件",
    "一次都没有",
    "它是我一个人",
    "搭的一条生产线",
    "吐出来的",
    "你想做自媒体",
    "多半卡在剪辑上",
    "写稿一小时",
    "剪片三小时",
    # 展开：四步
    "这条生产线",
    "把那三个小时",
    "砍到了三分钟",
    "第一步",
    "丢进一条对标视频",
    "AI 听写",
    "转成文字",
    "第二步",
    "结构级改写",
    "换钩子",
    "换案例",
    "不是换同义词",
    "第三步",
    "按关键词配画面",
    "图库自动找",
    "不够的",
    "AI 生图补",
    "第四步",
    "配音",
    "字幕",
    "一步到位",
    # 坑
    "坑也踩过",
    "C 盘满到装不下",
    "下载断流",
    "安装报错",
    "配音接口被封",
    "微软改了鉴权",
    "解法都是一句话",
    "重活全挪 E 盘",
    "配音换内置引擎",
    # 拿走
    "你能拿走的东西",
    "这套引擎开源",
    "十四万人点过 star",
    "一分钱不收",
    "我把踩过的坑",
    "整理成了一份文档",
    "照着抄就能跑通",
    # 收尾
    "做自媒体拼的",
    "不是工具新",
    "是管线稳",
    "一个人",
    "就是一条生产线",
    # 片尾：信源站 + 开源 + 关注钩子
    "这套系统怎么搭的",
    "我写成了完整档案",
    "连开源引擎一起",
    "地址在评论区",
    "顺便关注一下",
    "看我多久靠它赚到第一单",
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DUR.parent.mkdir(parents=True, exist_ok=True)
    durations = []
    env = {**os.environ, "MPT_HOME": str(MPT_HOME)}
    for i, line in enumerate(LINES, 1):
        cid = f"s-{i:02d}"
        dst = OUT / f"{cid}.mp3"
        if dst.exists() and dst.stat().st_size > 1000:
            p = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries",
                                "format=duration", "-of", "csv=p=0", str(dst)],
                               capture_output=True, text=True)
            d = float((p.stdout or "0").strip() or 0)
        else:
            r = subprocess.run(
                [str(MPT), "cli", "--video-script", line, "--video-source", "local",
                 "--stop-at", "audio", "--voice-name", VOICE, "--voice-rate", "1.15"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=300, cwd=str(BASE))
            m = re.search(r'"audio_file": "([^"]+)"', r.stdout or "")
            if not m:
                print(f"[{cid}] 失败: {(r.stderr or r.stdout or '')[-200:]}", flush=True)
                continue
            shutil.copyfile(Path(m.group(1)), dst)
            p = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries",
                                "format=duration", "-of", "csv=p=0", str(dst)],
                               capture_output=True, text=True)
            d = float((p.stdout or "0").strip() or 0)
        durations.append({"id": cid, "text": line, "duration": round(d, 3)})
        print(f"[{cid}] {d:.2f}s {line}", flush=True)

    DUR.write_text(json.dumps(durations, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(x["duration"] for x in durations)
    print(f"\n共 {len(durations)} 段 / {total:.1f}s / 平均 {total/max(1,len(durations)):.2f}s")


if __name__ == "__main__":
    main()
