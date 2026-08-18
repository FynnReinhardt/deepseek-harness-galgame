#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
webui_client.py — Forge Neo (A1111-compatible API) WebUI client for txt2img.

Zero third-party dependencies (stdlib urllib only). Requires the WebUI to be
launched with `--api` (see SKILL.md "启用 --api" section).

Endpoints used (A1111 standard, present in Forge Neo source modules/api/api.py):
    GET  /sdapi/v1/sd-models      list checkpoints
    GET  /sdapi/v1/options        read current options (incl. sd_model_checkpoint)
    POST /sdapi/v1/options        switch model / tweak options
    GET  /sdapi/v1/samplers       list samplers
    GET  /sdapi/v1/upscalers      list upscalers
    POST /sdapi/v1/txt2img        text-to-image (supports alwayson_scripts ADetailer)
    GET  /sdapi/v1/progress       current generation progress (0..1)
    POST /sdapi/v1/interrupt      cancel current generation

Usage (CLI):
    python webui_client.py status
    python webui_client.py models
    python webui_client.py switch "molKeunMix_anima.safetensors"
    python webui_client.py samplers
    python webui_client.py upscalers
    python webui_client.py txt2img --prompt "1girl, cat ears" \
        [--negative "bad anatomy"] [--size chibi|portrait|landscape|1024x1360] \
        [--cfg 7] [--steps 20] [--sampler "Euler a"] [--seed -1] \
        [--model "xxx.safetensors"] [--no-hires] [--ad-prompt "face, eyes"] \
        [--ad-denoise 0.4] [--outdir <dir>] [--no-progress]
    python webui_client.py progress
    python webui_client.py interrupt

Importable as a module:
    from webui_client import WebUIClient, PRESETS, DEFAULT_CFG, ...
    c = WebUIClient()
    c.list_models(); c.switch_model("x.safetensors"); c.txt2img(...)
"""
import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://127.0.0.1:7860"
# Images saved under <workspace>/outputs/webui by default
# (DSH workspace layout: outputs/ at workspace root, not under skills/)
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "outputs" / "webui"

# ---- user's fixed preset (2026-08-09) ----
PRESETS = {
    "chibi": (1024, 1024),      # 用于 chibi
    "portrait": (1024, 1360),   # 竖版
    "landscape": (1360, 1024),  # 横版
}
DEFAULT_CFG = 7.0
DEFAULT_SAMPLER = "Euler a"
DEFAULT_STEPS = 20
DEFAULT_HIRES = True        # 2026-08-14 用户测试后恢复：默认开启 Hires.fix
DEFAULT_SCHEDULER = "Automatic"
HR_UPSCALER = "4x-AnimeSharp"
HR_SCALE = 1.5
HR_DENOISE = 0.5            # 用户规格 0.4-0.6，取中值
HR_SECOND_PASS_STEPS = 10
AD_MODEL = "anime_face_m-seg.pt"
AD_CONFIDENCE = 0.3
AD_DENOISE = 0.4


class WebUIClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: int = 180):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    # ---------- low level ----------
    def _req(self, method: str, path: str, payload=None, timeout: int | None = None):
        url = self.base + path
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                raw = resp.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} {method} {path}: {body[:600]}") from e

    def _get(self, path, timeout=None):
        return self._req("GET", path, timeout=timeout)

    def _post(self, path, payload, timeout=None):
        return self._req("POST", path, payload, timeout=timeout)

    # ---------- capability checks ----------
    def api_available(self) -> bool:
        """True if the A1111-compatible API is mounted (server started with --api)."""
        try:
            self._get("/sdapi/v1/sd-models", timeout=5)
            return True
        except Exception:
            return False

    # ---------- models ----------
    def list_models(self):
        return self._get("/sdapi/v1/sd-models") or []

    def current_model(self) -> str:
        opts = self._get("/sdapi/v1/options")
        return opts.get("sd_model_checkpoint", "")

    def switch_model(self, name: str) -> str:
        """Switch checkpoint by title/name (case-sensitive). Returns confirmed model."""
        self._post("/sdapi/v1/options", {"sd_model_checkpoint": name})
        time.sleep(1.5)  # allow reload to settle
        cur = self.current_model()
        if cur != name:
            # some builds return short title; try matching by suffix
            if not cur.endswith(name) and not name.endswith(cur):
                raise RuntimeError(
                    f"Switch to {name!r} did not stick (now {cur!r}). "
                    f"Check exact name via 'models'."
                )
        return cur

    # ---------- misc lists ----------
    def list_samplers(self):
        return [s.get("name") for s in (self._get("/sdapi/v1/samplers") or [])]

    def list_upscalers(self):
        return [u.get("name") for u in (self._get("/sdapi/v1/upscalers") or [])]

    # ---------- progress / interrupt ----------
    def progress(self):
        return self._get("/sdapi/v1/progress")

    def interrupt(self):
        self._post("/sdapi/v1/interrupt", {})

    # ---------- txt2img ----------
    def build_payload(
        self,
        prompt: str,
        negative: str = "",
        size: tuple[int, int] = (1024, 1024),
        cfg: float = DEFAULT_CFG,
        steps: int = DEFAULT_STEPS,
        sampler: str = DEFAULT_SAMPLER,
        scheduler: str = DEFAULT_SCHEDULER,
        seed: int = -1,
        hires: bool = DEFAULT_HIRES,
        hires_denoise: float = HR_DENOISE,
        ad_prompt: str = "",
        ad_denoise: float = AD_DENOISE,
        ad_enabled: bool = True,
        model: str | None = None,
    ) -> dict:
        payload = {
            "prompt": prompt,
            "negative_prompt": negative,
            "width": size[0],
            "height": size[1],
            "cfg_scale": cfg,
            "steps": steps,
            "sampler_name": sampler,
            "scheduler": scheduler,
            "seed": seed,
            "batch_size": 1,
            "n_iter": 1,
        }
        if model:
            payload["override_settings"] = {"sd_model_checkpoint": model}

        if hires:
            payload.update({
                "enable_hr": True,
                "hr_scale": HR_SCALE,
                "hr_upscaler": HR_UPSCALER,
                "hr_second_pass_steps": HR_SECOND_PASS_STEPS,
                "denoising_strength": hires_denoise,
                "hr_resize_x": 0,
                "hr_resize_y": 0,
                # Forge Neo bug: API default is None -> "Use same choices" not in None
                # -> TypeError 'NoneType' is not iterable (modules/processing.py:1397)
                "hr_additional_modules": [],
            })

        if ad_enabled and ad_prompt.strip():
            payload["alwayson_scripts"] = {
                "ADetailer": {
                    "args": [{
                        "ad_model": AD_MODEL,
                        "ad_tab_enable": True,
                        "ad_prompt": ad_prompt.strip(),
                        "ad_negative_prompt": "",
                        "ad_confidence": AD_CONFIDENCE,
                        "ad_mask_filter_method": "Area",
                        "ad_mask_k": 0,
                        "ad_mask_min_ratio": 0.0,
                        "ad_mask_max_ratio": 1.0,
                        "ad_dilate_erode": 4,
                        "ad_x_offset": 0,
                        "ad_y_offset": 0,
                        "ad_mask_merge_invert": "None",
                        "ad_mask_blur": 4,
                        "ad_denoising_strength": ad_denoise,
                        "ad_inpaint_only_masked": True,
                        "ad_inpaint_only_masked_padding": 32,
                        "ad_use_inpaint_width_height": False,
                        "ad_inpaint_width": 512,
                        "ad_inpaint_height": 512,
                        "ad_use_steps": False,
                        "ad_steps": 20,
                        "ad_use_cfg_scale": False,
                        "ad_cfg_scale": 4.0,
                        "ad_use_checkpoint": False,
                        "ad_checkpoint": None,
                        "ad_use_vae": False,
                        "ad_vae": None,
                        "ad_use_sampler": False,
                        "ad_sampler": "Use same sampler",
                        "ad_scheduler": "Use same scheduler",
                        "ad_use_noise_multiplier": False,
                        "ad_noise_multiplier": 1.0,
                        "ad_restore_face": False,
                        "ad_controlnet_model": "None",
                        "ad_controlnet_module": "None",
                        "ad_controlnet_weight": 1.0,
                        "ad_controlnet_guidance_start_end": [0.0, 1.0],
                        "is_api": True,
                    }]
                }
            }
        return payload

    def txt2img(
        self,
        prompt: str,
        negative: str = "",
        size: tuple[int, int] = (1024, 1024),
        cfg: float = DEFAULT_CFG,
        steps: int = DEFAULT_STEPS,
        sampler: str = DEFAULT_SAMPLER,
        seed: int = -1,
        hires: bool = DEFAULT_HIRES,
        hires_denoise: float = HR_DENOISE,
        ad_prompt: str = "",
        ad_denoise: float = AD_DENOISE,
        model: str | None = None,
        outdir: str | Path | None = None,
        show_progress: bool = True,
        poll_interval: float = 0.8,
    ) -> dict:
        """Generate one image. Returns {path, info, seed, model, width, height}."""
        payload = self.build_payload(
            prompt=prompt, negative=negative, size=size, cfg=cfg, steps=steps,
            sampler=sampler, seed=seed, hires=hires, hires_denoise=hires_denoise,
            ad_prompt=ad_prompt, ad_denoise=ad_denoise,
            ad_enabled=bool(ad_prompt.strip()), model=model,
        )

        result = self._post("/sdapi/v1/txt2img", payload, timeout=1200)

        images = result.get("images") or []
        if not images:
            raise RuntimeError("txt2img returned no images")
        raw_b64 = images[0]
        if "," in raw_b64 and raw_b64.startswith("data:"):
            raw_b64 = raw_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)

        info = {}
        try:
            info = json.loads(result.get("info") or "{}")
        except Exception:
            pass
        used_model = info.get("sd_model_name") or model or ""
        used_seed = info.get("seed", seed)
        w, h = info.get("width", size[0]), info.get("height", size[1])

        outdir = Path(outdir) if outdir else OUTPUT_DIR
        outdir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        fname = f"{ts}-{used_model.replace('.safetensors','').replace(' ','_')}-s{used_seed}.png"
        path = outdir / fname
        path.write_bytes(img_bytes)

        return {
            "path": str(path),
            "info": info,
            "seed": used_seed,
            "model": used_model,
            "width": w,
            "height": h,
            "prompt": prompt,
        }

    def wait_done(self, poll_interval: float = 0.8, timeout: float = 1800):
        """Block until no active job. Returns final progress dict."""
        t0 = time.time()
        last = None
        while time.time() - t0 < timeout:
            p = self.progress()
            last = p
            prog = (p or {}).get("progress", 0.0) or 0.0
            eta = (p or {}).get("eta_relative")
            job = ((p or {}).get("state") or {}).get("job", "")
            sys.stdout.write(f"\r{prog*100:5.1f}% eta {eta if eta is not None else '?':>7} {job:<30}")
            sys.stdout.flush()
            if prog >= 1.0 or not ((p or {}).get("state") or {}).get("active", False):
                sys.stdout.write("\n")
                return p
            time.sleep(poll_interval)
        sys.stdout.write("\n")
        return last


def _parse_size(s: str) -> tuple[int, int]:
    if s in PRESETS:
        return PRESETS[s]
    if "x" in s.lower():
        w, h = s.lower().split("x", 1)
        return int(w), int(h)
    raise SystemExit(f"Unknown size: {s!r}. Use chibi|portrait|landscape or WxH.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="webui_client", description="Forge Neo txt2img client (A1111 API)")
    ap.add_argument("--url", default=DEFAULT_URL, help=f"WebUI base URL (default {DEFAULT_URL})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="check API availability + current model + samplers")
    sub.add_parser("models", help="list available checkpoints")
    sub.add_parser("samplers", help="list samplers")
    sub.add_parser("upscalers", help="list upscalers")
    sub.add_parser("progress", help="show current generation progress")
    sub.add_parser("interrupt", help="cancel current generation")

    p_switch = sub.add_parser("switch", help="switch checkpoint")
    p_switch.add_argument("model")

    p_t2i = sub.add_parser("txt2img", help="text-to-image generation")
    p_t2i.add_argument("--prompt", required=True)
    p_t2i.add_argument("--negative", default="")
    p_t2i.add_argument("--size", default="portrait", help="chibi|portrait|landscape|WxH (default portrait)")
    p_t2i.add_argument("--cfg", type=float, default=DEFAULT_CFG)
    p_t2i.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    p_t2i.add_argument("--sampler", default=DEFAULT_SAMPLER)
    p_t2i.add_argument("--seed", type=int, default=-1)
    p_t2i.add_argument("--model", default=None, help="override checkpoint for this run")
    p_t2i.add_argument("--no-hires", action="store_true", help="disable Hires.fix")
    p_t2i.add_argument("--hires-denoise", type=float, default=HR_DENOISE, help="Hires denoise 0.4-0.6")
    p_t2i.add_argument("--ad-prompt", default="", help="ADetailer face prompt (enables ADetailer)")
    p_t2i.add_argument("--ad-denoise", type=float, default=AD_DENOISE)
    p_t2i.add_argument("--outdir", default=None)
    p_t2i.add_argument("--no-progress", action="store_true", help="skip progress bar")

    args = ap.parse_args(argv)
    c = WebUIClient(args.url)

    if args.cmd == "status":
        if not c.api_available():
            print("A1111 API not mounted. Start Forge Neo with --api (see SKILL.md).")
            return 2
        print(f"OK  {args.url}")
        print(f"current model : {c.current_model()}")
        print(f"samplers      : {', '.join(c.list_samplers())}")
        print(f"upscalers     : {', '.join(c.list_upscalers())}")
        return 0

    if not c.api_available():
        print("A1111 API not mounted. Start Forge Neo with --api (see SKILL.md).")
        return 2

    if args.cmd == "models":
        for m in c.list_models():
            print(f"{m.get('model_name','?'):<45} {m.get('title','?'):<45} {m.get('sha256','')[:8]}")
        return 0

    if args.cmd == "samplers":
        print("\n".join(c.list_samplers()))
        return 0

    if args.cmd == "upscalers":
        print("\n".join(c.list_upscalers()))
        return 0

    if args.cmd == "progress":
        print(json.dumps(c.progress(), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "interrupt":
        c.interrupt()
        print("interrupt sent")
        return 0

    if args.cmd == "switch":
        cur = c.switch_model(args.model)
        print(f"now: {cur}")
        return 0

    if args.cmd == "txt2img":
        size = _parse_size(args.size)
        r = c.txt2img(
            prompt=args.prompt, negative=args.negative, size=size,
            cfg=args.cfg, steps=args.steps, sampler=args.sampler, seed=args.seed,
            hires=not args.no_hires, hires_denoise=args.hires_denoise,
            ad_prompt=args.ad_prompt, ad_denoise=args.ad_denoise,
            model=args.model, outdir=args.outdir,
            show_progress=not args.no_progress,
        )
        print(f"image : {r['path']}")
        print(f"model : {r['model']}")
        print(f"seed  : {r['seed']}")
        print(f"size  : {r['width']}x{r['height']}")
        print(f"hires : {'on' if not args.no_hires else 'off'}  ADetailer: {'on' if args.ad_prompt else 'off'}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
