# 高密度知识视频管道

一个人、一天、一毛钱，做完一条 100 秒的知识视频。

这套脚本把「写稿 → 配音 → 配画面 → 成片」串成一条线。不需要剪辑软件，不需要团队，不需要美术。

## 为什么做这个

2019 年，回形针做一条 5 分钟的知识视频，要 4-5 个人、2-4 周，摊到每条成本约 5.18 万元（来源：其公开财报，全年 80 条、总支出 414.4 万）。

现在这套管道：**1 个人、1 天、成本约 0.1 元**。

差的不是技术进步，是"知识可视化"这道墙塌了。

## 核心结论：密度比素材贵不贵重要

拆了一条同赛道爆款（662 秒 / 234 万赞）：

| 指标 | 对标 | 我们第一条 |
|---|---|---|
| 段数 | 370 | 55 |
| 每段时长 | **1.77 秒** | 1.82 秒 |
| 每段字数 | 9.2 字 | 10.1 字 |

之前做的是 10 张卡、每张 7.7 秒——**差 4.6 倍**。观众觉得闷，不是因为画面不好，是因为切得不够碎。

## 四步流程

```
① 写稿        N 段短句（每段 9-15 字，1.5-2.5 秒）
② 配音        make_audio.py  → durations.json
③ 排时间线    gen_timeline.py → timeline.json
④ 渲染        Remotion 组件（见下方）
```

配套素材脚本：

| 脚本 | 干什么 |
|---|---|
| `fetch_stock.py` | 从 Pixabay 抓视频素材（带标签/亮度/品牌三道过滤） |
| `fetch_images.py` | 从 Pixabay 抓竖版图片 |
| `seo_keywords.py` | 挖抖音/B站/百度搜索词，生成标题和标签 |
| `card_gen.py` | 把 JSON 渲染成 1920×1080 卡片 PNG（HTML → 截图） |

## 快速开始

```bash
# 1. 配音（需要 MPT 的 Edge TTS，或换成自己的 TTS）
export MPT_HOME=/path/to/mpt-home
python scripts/make_audio.py

# 2. 生成时间线
python scripts/gen_timeline.py

# 3. 抓素材
export PIXABAY_KEY=your_key   # 免费申请 https://pixabay.com/api/docs/
python scripts/fetch_stock.py
python scripts/fetch_images.py
```

## 渲染

时间线是给 [Remotion](https://github.com/remotion-dev/remotion) 用的。需要一个 `MixedCut` 组件把 `timeline.json` 渲染成视频，参考实现见 `docs/render.md`。

关键参数：

```bash
npx remotion render src/index.ts <composition-id> out/final.mp4
# 响度标准化（必须做，原始输出约 -24 LUFS，抖音里明显小声）
ffmpeg -i out/final.mp4 -c:v copy -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  -c:a aac -b:a 192k -movflags +faststart out/final-loud.mp4
```

## 踩过的坑（每条都是花钱买的）

1. **卡片模式与高密度节奏冲突**：标题入场动画要 22 帧，而每段只有 54 帧，动画没走完就切走了。高密度片别用卡片，用画面 + 字幕。
2. **fade 转场会叠层**：12 帧重叠但旧段不淡出，卡片和视频会糊在一起。高密度片一律 `cut`。
3. **深色素材 + 压暗 = 死黑**：`dim 0.55` 配暗素材整帧全黑，降到 0.22 才有画面。
4. **Pixabay 视频命中率约 50%，图片约 90%**：同样的词，图片质量高一个档次。搜 "warning light" 给全黑，搜 "building blocks" 给白底卡通。
5. **浅色 UI 截图不适合深色片**：6 张截图里 4 张是 90%+ 白像素，等于往片子里塞白板。
6. **字幕必须有描边或底条**：纯白字在浅色画面上完全隐形。

## 素材授权

Pixabay 素材遵循 [Pixabay License](https://pixabay.com/service/license-summary/)：可商用、无需署名。使用前仍需逐张肉眼验货——API 返回的素材有一半跑题、模糊或带水印。

## 预期效果与局限

- 适合：知识讲解、概念拆解、观点表达
- 不适合：需要真实人物出镜、需要精细调色的内容
- 免费素材的天花板很低：通用 B-roll 给不了"对得上话"的画面，自己的录屏才是独家

## License

MIT
