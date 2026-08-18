#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive_adventure.py — 把扮演段落归档为"冒险历史"并重建索引

流程 : 扮演每到一个段落结束 → 由 DSH 把该段扮演内容（对话+剧情）归档为 md
       → 存到 library/冒险历史/ → 重建向量索引 → 后续 RP 可检索"发生过什么"

用法 :
    python settings_rag/archive_adventure.py --title "云中城调查·第1段" --file rp_round.txt
    python settings_rag/archive_adventure.py --title "雨夜禁书区" --text "扮演内容直接作为参数传入"
    python settings_rag/archive_adventure.py --title "..." --file x.txt --no-build   # 只归档不重建

输出 : library/冒险历史/YYYYMMDD-HHMMSS-<title>.md
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT / "library" / "冒险历史"
BUILD = Path(__file__).resolve().parent / "build_index.py"


def slug(title: str) -> str:
    s = re.sub(r"[\\/:*?\"<>|\s]+", "-", title).strip("-")
    return s[:60] or "untitled"


def main() -> int:
    ap = argparse.ArgumentParser(description="归档扮演段落为冒险历史并重建索引")
    ap.add_argument("--title", required=True, help="段落标题（如：云中城调查·第1段）")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--file", help="扮演内容文件（UTF-8）")
    grp.add_argument("--text", help="扮演内容直接传入")
    ap.add_argument("--summary", default="", help="（可选）一句话摘要，写入文件头")
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    content = args.text if args.text is not None else Path(args.file).read_text(encoding="utf-8")
    ts = time.strftime("%Y%m%d-%H%M%S")
    target = HISTORY_DIR / f"{ts}-{slug(args.title)}.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    parts = [f"# 冒险历史：{args.title}", "", f"> 归档时间：{time.strftime('%Y-%m-%d %H:%M:%S')}"]
    if args.summary:
        parts += ["", f"> 摘要：{args.summary}"]
    parts += ["", "---", "", content.strip(), ""]
    target.write_text("\n".join(parts), encoding="utf-8")
    print(f"[+] 已归档: {target.relative_to(ROOT)}  ({len(content)} 字符)")

    if not args.no_build:
        print("[i] 重建向量索引 ...")
        env = dict(__import__("os").environ)
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run([sys.executable, str(BUILD)], env=env)
        if r.returncode != 0:
            print("[!] 索引重建失败")
            return r.returncode
        print("[+] 索引已更新，冒险历史已可检索")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
