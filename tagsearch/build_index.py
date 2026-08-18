#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py — 用 LM Studio bge-m3 给 Danbooru 标签建本地向量索引

数据源 : data/tags_enhanced.csv
        (来自 SAkizuki/DanbooruSearchOnline origin_database, GPL-3.0,
        仅收录 Danbooru 频数 >= 100 的 General/Character/Copyright 标签)
编码器 : LM Studio OpenAI 兼容 /v1/embeddings (text-embedding-bge-m3, 1024 维)
两路向量: en = "name, wiki" ; cn = cn_name
输出   : index/en.npy  index/cn.npy  (float16, L2 归一化) + index/meta.json

用法   : python build_index.py
"""
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "tags_enhanced.csv"
OUT = ROOT / "index"
LM_URL = "http://127.0.0.1:1234/v1/embeddings"
LM_MODEL = "text-embedding-bge-m3"
BATCH = 200


def embed(texts: list[str], timeout: int = 600) -> np.ndarray:
    body = json.dumps({"model": LM_MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        LM_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    rows = sorted(data["data"], key=lambda d: d["index"])
    out = np.zeros((len(rows), len(rows[0]["embedding"])), dtype=np.float32)
    for r in rows:
        out[r["index"]] = np.asarray(r["embedding"], dtype=np.float32)
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    out /= np.maximum(norms, 1e-8)  # L2 normalize
    return out


def main() -> int:
    if not SRC.is_file():
        print(f"[!] missing {SRC}")
        return 1
    rows = []
    with open(SRC, encoding="utf-8", newline="") as f:
        for rec in csv.DictReader(f):
            rows.append(rec)
    n = len(rows)
    print(f"[i] {n} tags loaded from {SRC.name}")

    en_texts, cn_texts = [], []
    for r in rows:
        name = (r.get("name") or "").strip()
        wiki = (r.get("wiki") or "").strip()
        cn = (r.get("cn_name") or "").strip()
        en_texts.append(name + (", " + wiki if wiki else ""))
        cn_texts.append(cn or name)

    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for layer, texts in (("en", en_texts), ("cn", cn_texts)):
        fname = OUT / f"{layer}.npy"
        if fname.is_file():
            print(f"[i] {fname.name} exists, skip")
            continue
        arrs = []
        for i in range(0, len(texts), BATCH):
            arrs.append(embed(texts[i : i + BATCH]))
            done = min(i + BATCH, n)
            el = time.time() - t0
            rate = done / el if el > 0 else 0
            eta = (n - done) / rate if rate > 0 else 0
            print(f"\r  {layer}: {done}/{n}  ({rate:.0f}/s, eta {eta:.0f}s)", end="", flush=True)
        print()
        mat = np.concatenate(arrs, axis=0).astype(np.float16)
        np.save(fname, mat)
        print(f"[+] {fname}  {mat.shape}  {mat.nbytes / 1e6:.0f} MB")

    meta = {
        "count": n,
        "dim": 1024,
        "model": LM_MODEL,
        "layers": ["en", "cn"],
        "source": "SAkizuki/DanbooruSearchOnline origin_database (GPL-3.0)",
        "tags": [
            {
                "name": r.get("name", ""),
                "cn_name": r.get("cn_name", ""),
                "wiki": (r.get("wiki") or "")[:200],
                "post_count": int(r.get("post_count") or 0),
                "category": int(r.get("category") or 0),
                "nsfw": int(r.get("nsfw") or 0),
            }
            for r in rows
        ],
    }
    with open(OUT / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    print(f"[+] meta.json  ({n} tags)")
    print(f"[done] total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
