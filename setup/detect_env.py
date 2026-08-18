#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detect_env.py — 环境检测（初始化流程第 2 步）

检测 : Python/numpy、绘画 WebUI（A1111/Forge API）、LM Studio、Ollama
输出 : 各项状态 + 缺失项建议（无 LM Studio → 引导装 Ollama）

用法 : python setup/detect_env.py
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config as cfg  # noqa: E402

EMBED_HINTS = ("bge-m3", "bge_m3", "nomic-embed", "embed")


def http_json(url: str, timeout: float = 6.0):
    req = urllib.request.Request(url, headers={"User-Agent": "dsh-setup/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "✅" if ok else "❌"
    print(f"{mark} {name:<14} {detail}")


def main() -> int:
    c = cfg.load()
    print("=" * 60)
    print("环境检测报告")
    print("=" * 60)

    # 1) Python + numpy
    try:
        import numpy as _np
        check("Python/numpy", True, f"python {sys.version.split()[0]}, numpy {_np.__version__}")
    except ImportError:
        check("Python/numpy", False, "需要 python3 + numpy：pip install numpy")

    # 2) 绘画 WebUI
    webui = c["webui_url"]
    try:
        models = http_json(webui.rstrip("/") + "/sdapi/v1/sd-models")
        names = [m.get("model_name", "?") for m in (models or [])][:6]
        check("绘画 WebUI", True, f"{webui}  模型: {', '.join(names)}{'...' if len(models or []) > 6 else ''}")
    except Exception as e:
        check("绘画 WebUI", False, f"{webui}  未检测到（{type(e).__name__}）。启动 A1111/Forge 并加 --api，或安装：https://github.com/AUTOMATIC1111/stable-diffusion-webui")

    # 3) LM Studio
    lm_url = c["embedding_url"].replace("/v1/embeddings", "")
    lm_found = False
    try:
        models = http_json(lm_url.rstrip("/") + "/v1/models")
        ids = [m.get("id", "") for m in models.get("data", [])]
        lm_found = True
        emb = [i for i in ids if any(h in i.lower() for h in EMBED_HINTS)]
        check("LM Studio", True, f"{lm_url}  模型: {', '.join(ids[:6])}")
        if emb:
            check("  ·嵌入模型", True, f"{emb[0]}")
        else:
            check("  ·嵌入模型", False, "未见 bge-m3/nomic-embed，请先在 LM Studio 加载嵌入模型")
    except Exception as e:
        check("LM Studio", False, f"{lm_url}  未检测到（{type(e).__name__}）")

    # 4) Ollama（备选）
    ola_found = False
    try:
        tags = http_json("http://127.0.0.1:11434/api/tags")
        ola_found = True
        names = [t.get("name", "") for t in tags.get("models", [])]
        emb = [n for n in names if any(h in n.lower() for h in EMBED_HINTS)]
        check("Ollama", True, f"http://127.0.0.1:11434  模型: {', '.join(names[:6])}")
        if emb:
            check("  ·嵌入模型", True, f"{emb[0]}")
        else:
            check("  ·嵌入模型", False, "未见嵌入模型，可执行：ollama pull bge-m3")
    except Exception as e:
        check("Ollama", False, "http://127.0.0.1:11434  未检测到")

    # 5) 建议
    print("-" * 60)
    problems = []
    if not lm_found and not ola_found:
        problems.append("向量服务缺失（LM Studio 与 Ollama 都没有）。二者选一即可，都未安装时推荐 Ollama（更轻量，纯命令行）：\n"
                        "    1) winget install Ollama.Ollama\n"
                        "    2) ollama pull bge-m3\n"
                        "    3) 运行 ollama serve，然后在 config.json 把 embedding_url 指向 http://127.0.0.1:11434/v1/embeddings、embedding_model 设为 bge-m3")
    elif ola_found and not lm_found:
        problems.append("使用 Ollama 即可（无需 LM Studio）。config.json: backend=ollama, embedding_url=http://127.0.0.1:11434/v1/embeddings, embedding_model=bge-m3")
    try:
        import numpy  # noqa: F401
    except ImportError:
        problems.append("缺少 numpy：pip install numpy（或用镜像 -i https://pypi.tuna.tsinghua.edu.cn/simple）")
    try:
        http_json(webui.rstrip("/") + "/sdapi/v1/sd-models", timeout=3)
    except Exception:
        problems.append("绘画 WebUI 不可用：请启动 A1111/Forge WebUI（带 --api），或安装 stable-diffusion-webui")

    if problems:
        print("需要处理：")
        for p in problems:
            print(f"  - {p}")
    else:
        print("全部就绪 ✅ 可直接进入下一步：导入设定集 → python settings_rag/import_docs.py")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
