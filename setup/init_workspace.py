#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_workspace.py — 新工作区初始化（初始化流程第 1 步）

作用 :
    1. 创建目录结构（characters/ settings/ novels/ import/ library/ outputs/webui/）
    2. 自动检测环境，生成 config.json（WebUI / 向量服务地址）
    3. 复制模板（角色卡规范/示例、导入说明）

用法 :
    python setup/init_workspace.py                 # 在当前目录初始化
    python setup/init_workspace.py --dir D:\novel  # 在指定目录初始化
    python setup/init_workspace.py --backend ollama  # 指定向量后端（auto=优先检测 LM Studio，否则 Ollama）
    python setup/init_workspace.py --webui-url http://127.0.0.1:7860
"""
import argparse
import json
import shutil
import sys
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES = SCRIPT_DIR / "templates"

DIRS = ["characters", "settings", "novels", "import", "library", "outputs/webui", "tagsearch/data"]


def http_ok(url: str, timeout: float = 4.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dsh-init/1.0"})
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        return False


def detect_backend() -> str:
    if http_ok("http://127.0.0.1:1234/v1/models"):
        return "lmstudio"
    if http_ok("http://127.0.0.1:11434/api/tags"):
        return "ollama"
    return "lmstudio"  # 默认，用户可后改


def main() -> int:
    ap = argparse.ArgumentParser(description="新工作区初始化")
    ap.add_argument("--dir", default=".", help="目标工作区目录（默认当前目录）")
    ap.add_argument("--backend", choices=["auto", "lmstudio", "ollama"], default="auto")
    ap.add_argument("--webui-url", default="http://127.0.0.1:7860")
    ap.add_argument("--embedding-url", default=None)
    ap.add_argument("--embedding-model", default=None)
    args = ap.parse_args()

    target = Path(args.dir).resolve()
    target.mkdir(parents=True, exist_ok=True)

    # 1) 目录
    for d in DIRS:
        (target / d).mkdir(parents=True, exist_ok=True)

    # 2) config.json
    backend = args.backend
    if backend == "auto":
        backend = detect_backend()
    if args.embedding_url:
        emb_url, emb_model = args.embedding_url, args.embedding_model or ""
    elif backend == "ollama":
        emb_url, emb_model = "http://127.0.0.1:11434/v1/embeddings", "bge-m3"
    else:
        emb_url, emb_model = "http://127.0.0.1:1234/v1/embeddings", "text-embedding-bge-m3"

    cfg = {
        "webui_url": args.webui_url,
        "embedding_url": emb_url,
        "embedding_model": emb_model,
        "llm_url": ("http://127.0.0.1:1234/v1/chat/completions" if backend == "lmstudio" else "http://127.0.0.1:11434/v1/chat/completions"),
        "llm_model": "",
        "output_dir": "outputs/webui",
        "char_dir": "characters",
        "backend": backend,
    }
    (target / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3) 模板
    copies = {
        "角色卡模板.md": "characters/角色卡模板.md",
        "characters_README.md": "characters/README.md",
        "import_README.md": "import/README.md",
    }
    for src, dst in copies.items():
        s = TEMPLATES / src
        if s.is_file():
            shutil.copyfile(s, target / dst)

    print(f"[+] 工作区已初始化: {target}")
    print(f"[+] 目录: {', '.join(DIRS)}")
    print(f"[+] config.json 已生成（backend={backend}）:")
    print(json.dumps(cfg, ensure_ascii=False, indent=2))
    print()
    print("下一步：")
    print(f"  1) 环境检测:    python setup/detect_env.py")
    print(f"  2) 导入设定集:  把素材放进 {target / 'import'}/ 后执行 python settings_rag/import_docs.py")
    print(f"  3) 建角色卡:    按 characters/README.md 格式创建 characters/<角色名>.md（或由 DSH 提取生成）")
    print(f"  4) 切换人格:    DSH 会话中调用 set_persona 工具（插件 pers-2）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
