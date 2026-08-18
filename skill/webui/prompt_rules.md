# WebUI 提示词构建规则（Anima 模型，2026-08-18 更新）

> 适用于 Forge Neo (127.0.0.1:7860) 的 Anima 系模型（molKeunMix_anima 等）。

## 优先级（强制）

1. **有角色卡**（`characters/<名>.md`）→ 身份 tag 直接取卡（角色tag/角色体形/角色面部），服装取 `--outfit`；**不再默认加 loli**，体形以卡为准
2. **场景/动作/背景一律用英文自然语言一段**（Anima 支持），**不用动作类 tag**
3. **与"主角"互动时**：加 `pov, solo focus`；不互动时删去
4. **背景 tag 默认不加**；只有场景不明确时才加 `simple background`
5. **本地向量化 danbooru 库始终参考**：NL 路径也会经 tagsearch 检索一批锚点 tag 拼在 NL 前（防幻觉、锚定道具/视觉元素）

## 正面词结构（顺序固定）

```
masterpiece, best quality, anime coloring,
<角色身份 tag（卡：角色tag + 体形 + 面部）>,
<服装 tag（卡：outfit）>,
[pov, solo focus]                      ← 与主角互动时
<本地 danbooru 库锚点 tag（--tag-count，默认 10）>,
<一段英文自然语言：场景 + 动作 + 背景 + 氛围>
```

- 质量词固定最前；身份 tag 永远不变（一致性关键）
- 英文描述示例：
  `In a base cafeteria, she shyly holds up a spoonful of curry toward you, cheeks flushed, fox ears twitching, warm indoor lighting, blurred dining hall in the background`
- 场景不明确时才追加：`simple background, white background, negative space`

## 负面词模板

```
worst quality, bad quality, bright pupils, empty eyes, blank eyes, fewer digits,
lowres, bad anatomy, bad hands, error, missing fingers, cropped, jpeg artifacts,
signature, watermark, username, blurry, chibi, deformed, oversized head, small head
```

- 固定：质量 + 面部 + 手部 + 防 Q 版（`chibi, deformed, oversized head, small head`）
- 画角类角色（dragon horns / sheep horns）时追加：`cow horns, demon horns, succubus horns, deer antlers`

## 分辨率

| 场景 | 分辨率 | 额外 |
|---|---|---|
| chibi（用户明确要 Q 版） | 1024 × 1024 | 仅此时才考虑 chibi |
| 其他（默认） | 1024 × 1360 | — |

## 实现

- `pipeline/generate.py` 已按此规则实现：`--scene-en` 英文描述、`--pov`、`--simple-bg`；默认打印完整提示词
- 无角色卡、纯 tag 场景（旧式）仍可用 `--desc` 回退

## 变更记录

- 2026-08-18：Anima 提示词规则大改——背景 tag 默认取消、动作/场景改英文自然语言、主角互动加 pov/solo focus、角色体形以角色卡为准（不再默认 loli）、负面词加防 Q 版。
