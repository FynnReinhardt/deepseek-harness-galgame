#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py — 项目配置加载（初始化后生成 config.json，未生成时用默认值）

字段 :
    webui_url        绘画 WebUI 地址（A1111/Forge 兼容 API）
    embedding_url    向量接口（LM Studio / Ollama 均 OpenAI 兼容 /v1/embeddings）
    embedding_model  嵌入模型名
    llm_url          （可选）本地 LLM 聊天接口
    llm_model        （可选）本地 LLM 模型名
    output_dir       立绘输出目录（相对项目根）
    char_dir         角色卡目录（相对项目根）
    backend          lmstudio | ollama
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEFAULTS = {
    "webui_url": "http://127.0.0.1:7860",
    "embedding_url": "http://127.0.0.1:1234/v1/embeddings",
    "embedding_model": "text-embedding-bge-m3",
    "llm_url": "http://127.0.0.1:1234/v1/chat/completions",
    "llm_model": "",
    "output_dir": "outputs/webui",
    "char_dir": "characters",
    "backend": "lmstudio",
    # Anima 模型配套（按本机实际路径填写）
    "anima_text_encoder": "",
    "anima_vae": "",
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    path = ROOT / "config.json"
    if path.is_file():
        try:
            cfg.update(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def path_of(key: str) -> Path:
    """把配置里的相对路径解析为绝对路径。"""
    p = load()[key]
    return Path(p) if Path(p).is_absolute() else ROOT / p
