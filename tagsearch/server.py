#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py — Danbooru 标签语义搜索 REST API（stdlib 实现，零第三方依赖）

接口 :
    GET /api/health            -> {"ok": true, "tags": N, "dim": 1024}
    GET /api/search?q=描述&limit=20&category=0|1|2&nsfw=0|1
                               -> {"query", "prompt", "results": [...]}
    GET /                      简单说明页

用法 : python server.py [--port 8100]
"""
import argparse
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from search import TagSearcher

searcher: TagSearcher | None = None


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path == "/api/health":
            return self._json({"ok": True, "tags": len(searcher.tags), "dim": int(searcher.en.shape[1])})
        if u.path == "/api/search":
            query = (q.get("q") or [""])[0].strip()
            if not query:
                return self._json({"error": "missing q"}, 400)
            try:
                limit = min(int((q.get("limit") or ["20"])[0]), 100)
            except ValueError:
                limit = 20
            cat = (q.get("category") or [None])[0]
            category = int(cat) if cat in ("0", "1", "2") else None
            nsfw = (q.get("nsfw") or ["0"])[0] == "1"
            results = searcher.search(query, limit=limit, category=category, show_nsfw=nsfw)
            prompt = ", ".join(r["name"] for r in results)
            return self._json({"query": query, "prompt": prompt, "results": results})
        if u.path == "/":
            return self._json({"service": "danbooru-tag-search", "api": ["/api/health", "/api/search?q=..."]})
        return self._json({"error": "not found"}, 404)

    def log_message(self, *args):
        pass


def main() -> int:
    global searcher
    ap = argparse.ArgumentParser(description="Danbooru tag search API")
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    print("[i] loading index ...")
    searcher = TagSearcher()
    print(f"[i] {len(searcher.tags)} tags ready")
    print(f"[+] API on http://{args.host}:{args.port}/api/search?q=...")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
