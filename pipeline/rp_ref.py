#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rp_ref.py — 组装"角色扮演参考上下文"（角色卡 + 设定/小说向量召回）

把以下三部分合成一个块，注入 RP 会话的 LLM 上下文：
  1. 角色卡性格（characters/，`--char` 指定）
  2. 设定集 + 小说正文的向量召回（settings_rag/index，`--query` 指定剧情要点）
  3. （可选）当前剧情/场景说明 `--scene`

用法 :
    python pipeline/rp_ref.py --char 龙娘 --query "雨夜 禁书区 龙语启示录" [--topk 4] [--scene "现在龙娘独自在禁书区"]
    python pipeline/rp_ref.py --char 龙娘 --query "天气与心情" --topk 2

输出 : 一个 markdown 参考块，可直接粘贴/注入为 RP 的 system 参考。
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "settings_rag"))

from characters import load_character  # noqa: E402
from retrieve import SettingsRetriever  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="组装角色扮演参考上下文")
    ap.add_argument("--char", required=True, help="角色名（characters/ 下的角色卡）")
    ap.add_argument("--query", required=True, help="需要参考的剧情要点/问题")
    ap.add_argument("--scene", default="", help="（可选）当前场景一句话")
    ap.add_argument("--topk", type=int, default=4)
    args = ap.parse_args()

    card = load_character(args.char)
    retriever = SettingsRetriever()
    hits = retriever.retrieve(args.query, topk=args.topk)

    out: list[str] = []
    out.append("# 角色扮演参考上下文")
    out.append("")
    out.append("## 角色卡")
    out.append(card.rp_prompt())
    if args.scene:
        out.append("")
        out.append("## 当前场景")
        out.append(args.scene)
    out.append("")
    out.append("## 设定/小说参考（向量召回）")
    if not hits:
        out.append("（无相关片段）")
    for i, h in enumerate(hits, 1):
        out.append(f"\n[{i}] {h['source']} / {h['heading']} (score={h['score']})")
        out.append(h["text"].strip())
    out.append("")
    out.append("> 扮演规则：言行严格贴合「角色卡·性格」；涉及设定细节时以上述参考为准；不得凭空发明与参考矛盾的事实。")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
