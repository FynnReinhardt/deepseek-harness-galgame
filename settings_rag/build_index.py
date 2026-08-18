#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py — 设定库向量检索：设定集/小说 → 分块 → LM Studio bge-m3 编码

输入 : 一个或多个目录下的 *.md / *.txt（角色设定、世界观、小说正文等，按 ## 标题分块）
输出 : index/chunks.json（原文块）+ index/vectors.npy（float16, L2 归一化）

用法 : python settings_rag/build_index.py [--src settings novels] [--out settings_rag/index]
"""
import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

import numpy as np

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
import config as _cfg  # noqa: E402

_CFG = _cfg.load()
LM_URL = _CFG.get("embedding_url", "http://127.0.0.1:1234/v1/embeddings")
LM_MODEL = _CFG.get("embedding_model", "text-embedding-bge-m3")
BATCH = 64
CHUNK_CHARS = 300  # 块目标长度（字符）
EXTS = (".md", ".txt")


def split_markdown(text: str, src: str) -> list[dict]:
    """按标题 + 段落拆分 markdown，产出 {text, source, heading} 块。"""
    lines = text.splitlines()
    chunks: list[dict] = []
    cur_heading = ""
    buf: list[str] = []

    def flush():
        nonlocal buf
        if not buf:
            return
        content = "\n".join(buf).strip()
        if content:
            chunks.append({"text": content, "source": src, "heading": cur_heading})
        buf = []

    for ln in lines:
        m = re.match(r"^(#{1,3})\s+(.+)$", ln)
        if m:
            flush()
            cur_heading = m.group(2).strip()
            continue
        buf.append(ln)
        # 超过目标长度即落块（按段落累积）
        if len("\n".join(buf)) >= CHUNK_CHARS:
            flush()
    flush()

    # 超长块（无标题的连续文本）按句子粗切
    out = []
    for c in chunks:
        if len(c["text"]) <= CHUNK_CHARS * 1.5:
            out.append(c)
            continue
        parts = re.split(r"(?<=[。！？.!?])", c["text"])
        piece, pieces = "", []
        for p in parts:
            if len(piece) + len(p) > CHUNK_CHARS and piece:
                pieces.append(piece)
                piece = ""
            piece += p
        if piece:
            pieces.append(piece)
        for p in pieces:
            p = p.strip()
            if p:
                out.append({**c, "text": p})
    return out


def embed(texts: list[str], timeout: int = 300) -> np.ndarray:
    body = json.dumps({"model": LM_MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(LM_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    rows = sorted(data["data"], key=lambda d: d["index"])
    out = np.zeros((len(rows), len(rows[0]["embedding"])), dtype=np.float32)
    for r in rows:
        out[r["index"]] = np.asarray(r["embedding"], dtype=np.float32)
    out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-8)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--src", nargs="+",
        default=[
            str(Path(__file__).resolve().parent.parent / "settings"),
            str(Path(__file__).resolve().parent.parent / "novels"),
            str(Path(__file__).resolve().parent.parent / "library"),
        ],
        help="一个或多个文档目录（默认 settings/ + novels/ + library/）",
    )
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "index"))
    args = ap.parse_args()
    out_dir = Path(args.out)

    files = []
    for d in args.src:
        for ext in EXTS:
            files.extend(Path(d).rglob(f"*{ext}"))
    files = sorted(set(files))
    if not files:
        print(f"[!] no docs found under {args.src} (exts {EXTS})")
        return 1
    chunks = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = f.read_text(encoding="gb18030")  # 部分中文文档是 GB18030
        rel = f.relative_to(next(p for p in (Path(x) for x in args.src) if str(f).startswith(str(p))))
        chunks.extend(split_markdown(text, str(rel)))
    print(f"[i] {len(files)} files -> {len(chunks)} chunks")

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    texts = [c["text"] for c in chunks]
    t0 = time.time()
    arrs = []
    for i in range(0, len(texts), BATCH):
        arrs.append(embed(texts[i : i + BATCH]))
        done = min(i + BATCH, len(texts))
        el = time.time() - t0
        rate = done / el if el > 0 else 0
        print(f"\r  {done}/{len(texts)}  ({rate:.0f}/s)", end="", flush=True)
    print()
    mat = np.concatenate(arrs, axis=0).astype(np.float16)
    np.save(out_dir / "vectors.npy", mat)
    print(f"[+] {out_dir / 'vectors.npy'}  {mat.shape}  {mat.nbytes / 1e6:.0f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
