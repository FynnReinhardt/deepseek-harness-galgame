#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_docs.py — 导入设定集/小说文档 → 整理为 md → 向量化建库

流程 :
    import/ 下的原始素材（单个文件 或 .zip 压缩包）
      → 1. 整理为 markdown（UTF-8），输出到 library/（独立目录，保留 zip 内部结构）
      → 2. 调用 build_index.py 重建向量库（RP 时可随时检索）

支持格式 : .txt .md .docx .pdf .html .htm .epub；.zip 内文件同样支持（docx/pdf/html 会转 md）

用法 :
    python settings_rag/import_docs.py                 # 处理 import/ 全部素材并重建索引
    python settings_rag/import_docs.py --src 某目录    # 指定来源目录
    python settings_rag/import_docs.py --no-build      # 只整理不建索引
    python settings_rag/import_docs.py --force         # 覆盖同名 md
"""
import argparse
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = ROOT / "import"
LIB_DIR = ROOT / "library"          # 整理好的数据（独立于示例 settings/novels/）
BUILD = Path(__file__).resolve().parent / "build_index.py"

CONVERT_EXT = (".docx", ".pdf", ".html", ".htm", ".epub")
COPY_EXT = (".md", ".txt")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def decode_bytes(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def read_text_any(path: Path) -> str:
    return decode_bytes(path.read_bytes())


def docx_to_md(data: bytes) -> str:
    root = ET.fromstring(zipfile.ZipFile(__import__("io").BytesIO(data)).read("word/document.xml"))
    out = []
    for p in root.iter(W + "p"):
        pPr = p.find(W + "pPr")
        style = ""
        if pPr is not None:
            ps = pPr.find(W + "pStyle")
            if ps is not None:
                style = (ps.get(W + "val") or "")
        text = "".join(t.text or "" for t in p.iter(W + "t")).strip()
        if not text:
            out.append("")
            continue
        if style.lower().startswith("heading"):
            m = re.search(r"(\d)", style)
            lvl = int(m.group(1)) if m else 1
            out.append("#" * min(lvl, 6) + " " + text)
        else:
            out.append(text)
    return "\n".join(out)


def pdf_to_md(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pypdf"], check=True)
        from pypdf import PdfReader
    reader = PdfReader(__import__("io").BytesIO(data))
    return "\n\n".join(pg.extract_text() or "" for pg in reader.pages)


def html_to_md(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", text)
    text = re.sub(
        r"(?i)<h([1-6])[^>]*>(.*?)</h\1>",
        lambda m: "#" * int(m.group(1)) + " " + re.sub(r"<[^>]+>", "", m.group(2)).strip(),
        text,
    )
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def epub_to_md(data: bytes) -> str:
    parts = []
    with zipfile.ZipFile(__import__("io").BytesIO(data)) as z:
        for n in z.namelist():
            if n.lower().endswith((".xhtml", ".html", ".htm")):
                parts.append(html_to_md(z.read(n).decode("utf-8", errors="replace")))
    return "\n\n".join(parts)


def to_md(data: bytes, ext: str) -> str | None:
    ext = ext.lower()
    if ext in COPY_EXT:
        return decode_bytes(data)
    if ext == ".docx":
        return docx_to_md(data)
    if ext == ".pdf":
        return pdf_to_md(data)
    if ext in (".html", ".htm"):
        return html_to_md(decode_bytes(data))
    if ext == ".epub":
        return epub_to_md(data)
    return None


def write_md(target: Path, text: str, force: bool) -> bool:
    if target.is_file() and not force:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return True


def import_zip(f: Path, force: bool) -> tuple[int, int]:
    done = skipped = 0
    dest_root = LIB_DIR / f.stem
    with zipfile.ZipFile(f) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            rel = Path(info.filename)
            if ".." in rel.parts or rel.is_absolute():
                print(f"[!] 跳过不安全路径: {info.filename}")
                continue
            # 去掉与 zip 同名的一层冗余目录（zip 根文件夹 = 包名时）
            if rel.parts and rel.parts[0] == f.stem:
                rel = Path(*rel.parts[1:])
            if not rel.parts:
                continue
            ext = rel.suffix.lower()
            if ext not in COPY_EXT and ext not in CONVERT_EXT:
                continue
            data = z.read(info)
            if ext in CONVERT_EXT:
                md = to_md(data, ext)
                if md is None:
                    continue
                target = dest_root / rel.with_suffix(".md")
                text = md
            else:
                target = dest_root / rel
                text = decode_bytes(data)
            if write_md(target, text, force):
                print(f"[+] {f.name}!/{rel} -> {target.relative_to(ROOT)}")
                done += 1
            else:
                skipped += 1
    return done, skipped


def import_loose(f: Path, force: bool) -> tuple[int, int]:
    ext = f.suffix.lower()
    md = to_md(f.read_bytes(), ext)
    if md is None:
        return 0, 0
    target = LIB_DIR / f"{f.stem}.md"
    if write_md(target, md, force):
        print(f"[+] {f.name} -> {target.relative_to(ROOT)}  ({len(md)} 字符)")
        return 1, 0
    print(f"[~] 已存在（--force 覆盖）: {target.relative_to(ROOT)}")
    return 0, 1


def main() -> int:
    ap = argparse.ArgumentParser(description="导入设定/小说素材并建向量库")
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    src_dir = Path(args.src)
    if not src_dir.is_dir():
        print(f"[!] 目录不存在: {src_dir}")
        return 1

    files = sorted(
        p for p in src_dir.iterdir()
        if p.is_file()
        and p.name.lower() != "readme.md"
        and (p.suffix.lower() == ".zip" or p.suffix.lower() in COPY_EXT or p.suffix.lower() in CONVERT_EXT)
    )
    if not files:
        print(f"[i] {src_dir} 下没有可导入的素材（zip/txt/md/docx/pdf/html/epub）")
        return 1

    done = skipped = 0
    for f in files:
        if f.suffix.lower() == ".zip":
            d, s = import_zip(f, args.force)
        else:
            d, s = import_loose(f, args.force)
        done += d
        skipped += s
    print(f"\n[i] 整理 {done} 个，跳过 {skipped} 个 -> {LIB_DIR.relative_to(ROOT)}/")

    if not args.no_build and done:
        print("[i] 重建向量索引 ...")
        env = dict(__import__("os").environ)
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run([sys.executable, str(BUILD)], env=env)
        if r.returncode != 0:
            print("[!] 索引重建失败")
            return r.returncode
        print("[+] 索引已更新，可在 RP 中随时检索")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
