#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search.py — 自然语言 → Danbooru 标签 语义搜索（完全本地）

依赖 : 系统 python + numpy；索引由 build_index.py 生成；查询编码走 LM Studio bge-m3
用法 :
    python search.py "穿着白色水手服的少女在雨中奔跑"
    python search.py "金发双马尾" --limit 10 --category 0
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
import config as _cfg  # noqa: E402

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index"
_CFG = _cfg.load()
LM_URL = _CFG.get("embedding_url", "http://127.0.0.1:1234/v1/embeddings")
LM_MODEL = _CFG.get("embedding_model", "text-embedding-bge-m3")

EN_W = 0.6        # 英文层权重（cn 层为 1-EN_W）
POP_W = 0.15      # 热度加成强度（log 归一化后乘此权重）


class TagSearcher:
    def __init__(self, index_dir: Path = INDEX):
        self.en = np.load(index_dir / "en.npy").astype(np.float32)
        cn_path = index_dir / "cn.npy"
        if cn_path.is_file():
            self.cn = np.load(cn_path).astype(np.float32)
            self.en_w = EN_W
        else:
            # cn 层未构建时退化为纯英文层（日志提示）
            self.cn = None
            self.en_w = 1.0
            print("[warn] cn.npy missing -> en-only mode", file=sys.stderr)
        with open(index_dir / "meta.json", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.tags = self.meta["tags"]
        pops = np.log1p(np.array([t["post_count"] for t in self.tags], dtype=np.float32))
        self.pop_norm = pops / pops.max()

    def embed_query(self, text: str) -> np.ndarray:
        body = json.dumps({"model": LM_MODEL, "input": [text]}).encode("utf-8")
        req = urllib.request.Request(
            LM_URL, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        v = np.asarray(data["data"][0]["embedding"], dtype=np.float32)
        norm = np.linalg.norm(v)
        return v / max(norm, 1e-8)

    def search(
        self,
        text: str,
        limit: int = 20,
        category: int | None = None,
        show_nsfw: bool = False,
    ) -> list[dict]:
        q = self.embed_query(text)
        sim_en = self.en @ q
        sim_cn = sim_en if self.cn is None else self.cn @ q
        score = self.en_w * sim_en + (1 - self.en_w) * sim_cn + POP_W * self.pop_norm
        order = np.argsort(-score)
        out = []
        for idx in order:
            t = self.tags[idx]
            if category is not None and t["category"] != category:
                continue
            if not show_nsfw and t["nsfw"]:
                continue
            out.append({**t, "score": round(float(score[idx]), 4)})
            if len(out) >= limit:
                break
        return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Danbooru tag 语义搜索（本地 LM Studio）")
    ap.add_argument("query", help="自然语言描述，如：穿着白色水手服的少女")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument(
        "--category", choices=["0", "1", "2"], default=None,
        help="0=General 1=Character 2=Copyright",
    )
    ap.add_argument("--nsfw", action="store_true", help="包含 NSFW 标签")
    args = ap.parse_args()

    s = TagSearcher()
    res = s.search(
        args.query,
        limit=args.limit,
        category=int(args.category) if args.category else None,
        show_nsfw=args.nsfw,
    )
    if not res:
        print("(no results)")
        return 0
    for r in res:
        print(
            f"{r['score']:>7.4f}  {r['name']:<45} "
            f"{str(r['cn_name'])[:18]:<20} posts={r['post_count']:<8} "
            f"cat={r['category']}{' NSFW' if r['nsfw'] else ''}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
