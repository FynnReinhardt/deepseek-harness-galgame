#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retrieve.py — 设定库检索：给定剧情/问题上下文，召回最相关的设定块

用法 :
    python settings_rag/retrieve.py "女主的发色和性格是什么"
    python settings_rag/retrieve.py "当前场景需要知道的世界观设定" --topk 5
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
import config as _cfg  # noqa: E402

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index"
_CFG = _cfg.load()
LM_URL = _CFG.get("embedding_url", "http://127.0.0.1:1234/v1/embeddings")
LM_MODEL = _CFG.get("embedding_model", "text-embedding-bge-m3")


class SettingsRetriever:
    def __init__(self, index_dir: Path = INDEX):
        with open(index_dir / "chunks.json", encoding="utf-8") as f:
            self.chunks = json.load(f)
        self.vectors = np.load(index_dir / "vectors.npy").astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        body = json.dumps({"model": LM_MODEL, "input": [text]}).encode("utf-8")
        req = urllib.request.Request(LM_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        v = np.asarray(data["data"][0]["embedding"], dtype=np.float32)
        norm = np.linalg.norm(v)
        return v / max(norm, 1e-8)

    def retrieve(self, query: str, topk: int = 4) -> list[dict]:
        q = self.embed_query(query)
        sims = self.vectors @ q
        order = np.argsort(-sims)
        return [
            {**self.chunks[i], "score": round(float(sims[i]), 4)}
            for i in order[:topk]
            if float(sims[i]) > 0.2  # 低相关块丢弃
        ]


def main() -> int:
    ap = argparse.ArgumentParser(description="设定库语义检索")
    ap.add_argument("query", help="检索问题/剧情上下文")
    ap.add_argument("--topk", type=int, default=4)
    args = ap.parse_args()
    r = SettingsRetriever()
    res = r.retrieve(args.query, topk=args.topk)
    if not res:
        print("(no relevant chunks)")
        return 0
    for i, c in enumerate(res, 1):
        print(f"--- [{i}] score={c['score']}  src={c['source']}  heading={c['heading']} ---")
        print(c["text"][:300])
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
