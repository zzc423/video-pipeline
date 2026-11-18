# 渲染对接说明

`timeline.json` 是一个**数据契约**，渲染层可以自己实现。本文说明每个字段的含义和一份最小可用的 React 实现思路。

## timeline.json 结构

```jsonc
{
  "slug": "video-line-001",
  "title": "这条视频，成本一毛钱",
  "format": { "w": 1080, "h": 1920, "fps": 30 },
  "voice": { "id": "zh-CN-YunxiNeural", "speed": 1.15, "enabled": true },
  "chapters": [{ "label": "开场", "from": "s-01", "to": "s-12" }],
  "segments": [
    {
      "id": "s-01",
      "narration": "为什么你越努力",       // 配音文本
      "frames": 54,                        // 本段帧数
      "transition": "cut",                 // cut / fade / slide
      "visual": { ... },                   // 画面（见下）
      "caption": {                         // 字幕
        "style": "subtitle",               // subtitle / big_word / highlight / none
        "text": "为什么你越努力",
        "highlight": ["越努力"]             // 高亮词（数组）
      }
    }
  ]
}
```

## visual 的四种类型

```jsonc
// 1. 视频素材
{ "kind": "video", "src": "assets/broll/x.mp4", "motion": "kenburns_in", "dim": 0.22 }

// 2. 图片素材（带缓慢推拉，让静态图"活着"）
{ "kind": "image", "src": "assets/photos/x.jpg", "motion": "pan_right", "dim": 0.18 }

// 3. 截图（装进浏览器框 / 手机机身）
{ "kind": "screenshot", "screenshot": {
    "src": "assets/screenshot/x.png",
    "frame": "browser",       // browser | phone | none
    "focus": "center",        // top | center | bottom（长截图取哪段）
    "zoom": 1.1,
    "url": "地址栏文字"
} }

// 4. 整屏卡片（慎用：段长 <2 秒时标题动画来不及）
{ "kind": "card", "card": {
    "preset": "night",        // paper | ink | blue | night
    "kicker": "小标签",
    "head": "主标题",
    "sub": "副标题",
    "chips": ["药丸", "标签"],  // 可选图解
    "bars": [{ "label": "写稿", "value": 1, "caption": "1 小时" }],
    "rows": [{ "k": "重活", "v": "全挪 E 盘" }]
} }
```

`motion` 取值：`kenburns_in` / `kenburns_out` / `pan_left` / `pan_right` / `none`

## 时间轴计算（关键）

```
cursor = 0
for seg in segments:
    from = cursor
    cursor += seg.frames - (0 if seg.transition == "cut" else 12)
```

**`fade` / `slide` 会重叠 12 帧**，`cut` 不重叠。

这个偏移必须同时用在两处：
1. 画面 Sequence 的 `from`
2. 配音 Audio 的 `from`

两边算错任意一处，音画就不同步。

## 一份最小实现（Remotion）

```tsx
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile } from "remotion";
import timeline from "./timeline.json";

const XF = 12;

export const Video: React.FC = () => {
  let cursor = 0;
  return (
    <AbsoluteFill style={{ background: "#05080C" }}>
      {timeline.segments.map((seg) => {
        const from = cursor;
        cursor += seg.frames - (seg.transition === "cut" ? 0 : XF);
        const v = seg.visual;
        return (
          <Sequence key={seg.id} from={from} durationInFrames={seg.frames}>
            {v.kind === "video"
              ? <OffthreadVideo src={staticFile(v.src)} muted />
              : <Img src={staticFile(v.src ?? v.screenshot?.src)} />}
            <Audio src={staticFile(`audio/${seg.id}.mp3`)} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
```

这是最简版，没有 Ken Burns、没有字幕、没有设备框。完整效果参考 [Remotion 官方文档](https://www.remotion.dev/docs/)。

## 两条必须遵守的规矩

1. **每段开头 3 帧内必须有内容**——否则黑帧检测会报警，观感也差
2. **字幕必须加描边或底条**——纯白字在浅色画面上等于没有
