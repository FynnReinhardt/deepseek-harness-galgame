---
name: webui
description: 调用本机 Forge Neo（Stable Diffusion WebUI）做文生图。用户提到"画一张/生成图片/WebUI/换模型/出图/推图"，或要求用 anime 系模型出图、调 CFG/steps/分辨率/Hires.fix/ADetailer 时使用。先确认后台 API 可用（--api），再列模型、切换模型、按用户参数生成，图片保存到 outputs/webui/ 并在回复中给出路径。
---

# WebUI 文生图（Forge Neo / A1111 兼容 API）

调用本机 Forge Neo（`http://127.0.0.1:7860/`）的 A1111 标准 API 做**文生图**，支持模型切换、参数调整、Hires.fix、ADetailer，生成图片保存后告知用户路径。

## 前置条件

**后台必须带 `--api` 启动**，否则 `/sdapi/v1/*` 全部 404。

检查方法（在 `skill/webui` 目录下）：

```powershell
python scripts/webui_client.py status
```

- 返回 `OK` → 可直接用。
- 返回 `A1111 API not mounted` → 需要给 Forge Neo 启动参数加 `--api` 并重启。**重启是破坏性操作，先与用户确认再执行**，重启后模型重新加载、首次出图较慢。

## 模型配置（重要）

本机有两类模型，加载方式完全不同：

1. **XL 系**：`molKeunMix_deepcobalt`（光辉）——模型内嵌 VAE，`sd_vae` 保持 `Automatic`，直接 `switch` 即可使用。
2. **Anima 系**：`molKeunMix_anima`、`uwumergeAnimaEditionCute_v40/v50`、`dasiwaAnima_obsidianArchivesV2`——**必须**配套 Qwen CLIP + Qwen VAE 才能出图：
   - CLIP：`models/text_encoder/qwen_3_06b_base.safetensors`
   - VAE：`models/VAE/qwen_image_vae.safetensors`
   - 通过 `override_settings` 的 `forge_additional_modules` 传入**完整路径**（与 Forge 内置 PiD 扩展同一机制）。
   - 常见报错：缺配套时 `You do not have VAE state dict!`；只设 `sd_vae` 而模型仍是 XL 架构时 `corrupt or invalid`（VAE 架构不匹配）。

### Anima 出图 payload 示例（curl）

```json
{
  "prompt": "masterpiece, best quality, anime coloring, 1girl, ...",
  "negative_prompt": "worst quality, bad quality, ...",
  "steps": 20, "cfg_scale": 7, "width": 1024, "height": 1360,
  "sampler_name": "Euler a",
  "override_settings": {
    "sd_model_checkpoint": "molKeunMix_anima.safetensors",
    "forge_additional_modules": [
      "F:\\sd-webui-forge-neo\\models\\VAE\\qwen_image_vae.safetensors",
      "F:\\sd-webui-forge-neo\\models\\text_encoder\\qwen_3_06b_base.safetensors"
    ]
  }
}
```

> 注：`webui_client.py` 当前不支持 `forge_additional_modules`（Anima 系需用 curl 或后续扩展脚本）。

## 提示词构建规则（强制）

完整规则见同目录 `prompt_rules.md`，所有文生图必须遵守。要点：中文描述 → Danbooru（非 furry）/ e621（furry）tag；质量词开头、背景词结尾；默认 `loli`；负面词按模板（loli 追加 `aged up, mature female, 1boy, muscular, shota`）。

## 用户固定参数规格

| 项 | 值 |
|---|---|
| 分辨率 | `chibi`=1024x1024、`portrait`=1024x1360、`landscape`=1360x1024 |
| CFG | 7 |
| 采样器 / 步数 | Euler a / 20 |
| Hires.fix | 算法 `4x-AnimeSharp`，放大 1.5x，重绘 0.4-0.6（默认 0.5），二阶段 10 步 |
| ADetailer | 模型 `anime_face_m-seg.pt`，脸部提示词非空即启用 |

默认值已内置在 `webui_client.py`，用户没特别说就用这套。

## 常用命令（在 `skill/webui` 目录下运行）

```powershell
# 状态 / 模型 / 切换（XL 系）
python scripts/webui_client.py status
python scripts/webui_client.py models
python scripts/webui_client.py switch "molKeunMix_anima.safetensors"

# 生成（默认 portrait 1024x1360, CFG7, Euler a, 20步, Hires 1.5x）
python scripts/webui_client.py txt2img --prompt "1girl, cat ears, chibi" --size chibi
python scripts/webui_client.py txt2img --prompt "..." --ad-prompt "face, detailed eyes"   # 带 ADetailer
python scripts/webui_client.py txt2img --prompt "..." --size landscape --cfg 12 --seed 12345

# 进度 / 中断
python scripts/webui_client.py progress
python scripts/webui_client.py interrupt
```

## 对话工作流

1. 用户要图 → `status` 确认 API 可用。
2. 切换模型：XL 系用 `switch`；Anima 系需带 `forge_additional_modules`（脚本暂不支持，用 curl 示例）。
3. 按「提示词构建规则」拼 prompt → **先发用户确认画面大概内容**（默认不展示提示词和参数）→ 用户说开始后调用 txt2img。
4. 交图：图片保存到 `outputs/webui/`（脚本自动建目录），回复中给完整文件路径。
5. 默认不展示 seed/模型/参数，用户要求时才展示；出图后直接交图，不做视觉质检（用户确认）。

## 注意事项

- 只做**文生图**，不做图生图/ControlNet/超分工作流。
- 不要擅自改固定参数规格；用户覆盖时以用户为准并在回复里注明。
- Anima 系首次加载（含 Qwen CLIP + VAE）较慢属正常，可用 `progress` 看进度。
