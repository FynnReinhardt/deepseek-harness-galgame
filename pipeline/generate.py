#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 端到端立绘生成：自然语言描述 → Danbooru tags → Forge Neo WebUI

链路 :
    中文/英文描述
      -> TagSearcher（tagsearch/index, LM Studio bge-m3 编码）
      -> Danbooru tag 列表
      -> A1111 兼容 txt2img（Anima 模型 + Qwen CLIP/VAE override_settings）
      -> PNG 保存到 outputs/webui/

用法 :
    python pipeline/generate.py --desc "穿着白色水手服的蓝发少女，站在雨中"
    python pipeline/generate.py --desc "金发双马尾女仆" --model uwumergeAnimaEditionCute_v50 --size portrait
    # --confirm 时先打印画面与 tags 预览，回车确认后才出图（配合"先确认后出图"流程）
"""
import argparse
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np  # noqa: F401  (保持与 tagsearch 一致的环境)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tagsearch"))

from search import TagSearcher  # noqa: E402

from characters import load_character  # noqa: E402

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
import config as _cfg  # noqa: E402

_CFG = _cfg.load()
WEBUI_URL = _CFG.get("webui_url", "http://127.0.0.1:7860")
OUT_DIR = _cfg.path_of("output_dir")

# ---- 固定质量词 / 负面词模板 ----
QUALITY = "masterpiece, best quality, anime coloring"
BG = "simple background, white background, negative space"  # 仅 --simple-bg 时使用（场景不明确才加）
NEGATIVE = (
    "worst quality, bad quality, bright pupils, empty eyes, blank eyes, "
    "fewer digits, lowres, bad anatomy, bad hands, error, missing fingers, "
    "cropped, jpeg artifacts, signature, watermark, username, blurry, "
    "chibi, deformed, oversized head, small head"
)

# ---- Anima 系模型：必须带 Qwen CLIP + VAE（Forge override_settings）----
# clip/vae 路径来自 config.json（anima_clip/anima_vae）；为空时回退本机路径
_CFG_CLIP = (_CFG.get("anima_clip") or "").strip()
_CFG_VAE = (_CFG.get("anima_vae") or "").strip()
ANIMA_MODULES = {
    "molKeunMix_anima": {
        "clip": _CFG_CLIP or r"F:\sd-webui-forge-neo\models\text_encoder\qwen_3_06b_base.safetensors",
        "vae": _CFG_VAE or r"F:\sd-webui-forge-neo\models\VAE\qwen_image_vae.safetensors",
    },
    "uwumergeAnimaEditionCute_v50": {
        "clip": _CFG_CLIP or r"F:\sd-webui-forge-neo\models\text_encoder\qwen_3_06b_base.safetensors",
        "vae": _CFG_VAE or r"F:\sd-webui-forge-neo\models\VAE\qwen_image_vae.safetensors",
    },
    "uwumergeAnimaEditionCute_v40": {
        "clip": _CFG_CLIP or r"F:\sd-webui-forge-neo\models\text_encoder\qwen_3_06b_base.safetensors",
        "vae": _CFG_VAE or r"F:\sd-webui-forge-neo\models\VAE\qwen_image_vae.safetensors",
    },
    "dasiwaAnima_obsidianArchivesV2": {
        "clip": _CFG_CLIP or r"F:\sd-webui-forge-neo\models\text_encoder\qwen_3_06b_base.safetensors",
        "vae": _CFG_VAE or r"F:\sd-webui-forge-neo\models\VAE\qwen_image_vae.safetensors",
    },
}

SIZES = {"chibi": (1024, 1024), "portrait": (1024, 1360), "landscape": (1360, 1024)}


def txt2img_anima(
    prompt: str,
    negative: str,
    model: str,
    size: tuple[int, int],
    cfg: float = 7.0,
    steps: int = 20,
    sampler: str = "Euler a",
    seed: int = -1,
    timeout: int = 900,
) -> dict:
    """调用 Forge Neo，Anima 模型必须带 Qwen CLIP/VAE override_settings。"""
    mod = ANIMA_MODULES[model]
    payload = {
        "prompt": prompt,
        "negative_prompt": negative,
        "width": size[0],
        "height": size[1],
        "cfg_scale": cfg,
        "steps": steps,
        "sampler_name": sampler,
        "seed": seed,
        "batch_size": 1,
        "n_iter": 1,
        "override_settings": {
            "sd_model_checkpoint": f"{model}.safetensors",
            "forge_additional_modules": [mod["vae"], mod["clip"]],
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        WEBUI_URL + "/sdapi/v1/txt2img",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"txt2img returned no images: {result.get('error') or result}")
    raw = images[0]
    if "," in raw and raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    return {"png": base64.b64decode(raw), "info": result.get("info", "")}


def build_prompt(
    tags: list[dict],
    card=None,
    outfit: str | None = None,
    scene_en: str = "",
    pov: bool = False,
    simple_bg: bool = False,
) -> tuple[str, str]:
    """组装 Anima 提示词：
    质量词 + 角色身份(固定) + 服装(可换) + [pov, solo focus] + 场景
    场景：优先用英文自然语言描述（--scene-en）；否则回退场景 tags（--desc 检索）。
    背景 tag 默认不加，仅 --simple-bg（场景不明确时）。
    """
    tag_parts = [QUALITY]
    if card is not None:
        tag_parts.append(card.identity_tags)
        tag_parts.append(card.outfit_tags(outfit))
    if pov:
        tag_parts.append("pov, solo focus")
    if simple_bg:
        tag_parts.append(BG)
    tags_str = ", ".join(p for p in tag_parts if p)

    scene_en = (scene_en or "").strip()
    if scene_en:
        pos = tags_str + "\n" + scene_en
    else:
        scene = ", ".join(t["name"] for t in tags[:20])
        pos = tags_str + (", " + scene if scene else "")
    return pos, NEGATIVE


def main() -> int:
    ap = argparse.ArgumentParser(description="端到端立绘生成（Anima 模型）")
    ap.add_argument("--desc", default=None, help="中文场景描述（用于 tagsearch；有 --scene-en 时可省）")
    ap.add_argument("--scene-en", default="", help="英文自然语言场景/动作描述（Anima 支持，替代动作类 tag）")
    ap.add_argument("--pov", action="store_true", help="与主角互动视角：加 pov, solo focus")
    ap.add_argument("--simple-bg", action="store_true", help="场景不明确时加 simple background")
    ap.add_argument("--char", default=None, help="角色名（characters/ 下的角色卡，固定身份 tag）")
    ap.add_argument("--outfit", default=None, help="角色服装名（默认第一套）")
    ap.add_argument("--model", default="molKeunMix_anima", choices=list(ANIMA_MODULES))
    ap.add_argument("--size", default="portrait", choices=list(SIZES))
    ap.add_argument("--limit", type=int, default=20, help="回退场景 tag 数量")
    ap.add_argument("--category", choices=["0", "1", "2"], default=None)
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    if not args.desc and not args.scene_en.strip():
        ap.error("需要 --desc（中文场景）或 --scene-en（英文场景描述）至少一个")

    card = None
    if args.char:
        card = load_character(args.char)
        outfit_name = args.outfit or card.list_outfits()[0]
        print(f"[0/3] 角色卡: {card.name}  服装: {outfit_name}（可选: {card.list_outfits()}）")
        print(f"      固定身份tag: {card.identity_tags}")

    tags = []
    if args.desc:
        print("[1/3] 语义检索 Danbooru tags（场景/道具）...")
        s = TagSearcher()
        tags = s.search(
            args.desc,
            limit=args.limit,
            category=int(args.category) if args.category else None,
            show_nsfw=False,
        )
        print(f"      top tags: {', '.join(r['name'] for r in tags[:12])} ...")

    prompt, negative = build_prompt(
        tags, card=card, outfit=args.outfit,
        scene_en=args.scene_en, pov=args.pov, simple_bg=args.simple_bg,
    )
    print("\n--- 提示词 ---")
    print(f"Prompt  : {prompt}")
    print(f"Negative: {negative}")
    print(f"模型    : {args.model}  {args.size} {SIZES[args.size]}")

    print(f"[2/3] Forge Neo 出图（{args.model} + Qwen CLIP/VAE）...")
    t0 = time.time()
    img = txt2img_anima(prompt, negative, args.model, SIZES[args.size], seed=args.seed)
    print(f"      generated in {time.time() - t0:.0f}s")

    outdir = Path(args.outdir) if args.outdir else OUT_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = outdir / f"{ts}-{args.model}-s{args.seed}.png"
    path.write_bytes(img["png"])
    print(f"[3/3] saved: {path}  ({len(img['png'])} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
