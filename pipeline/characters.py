#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
characters.py — 角色卡解析（立绘一致性核心）

格式见 characters/README.md：
    角色名字：xxx
    角色tag：（IP tag 或 <lora:xxx:0.8>，可空）
    角色体形：petite, small breasts
    角色面部：white hair, ...
    角色衣服：
    - 默认: yellow sweater vest, ...
    - 泳装: swimsuit, ...
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAR_DIR = ROOT / "characters"

KEYS = ("角色名字", "角色tag", "角色体形", "角色面部", "角色衣服", "角色性格")
# 自由文本字段（多行续行按换行连接，而非逗号）
FREE_TEXT = {"角色性格"}


class CharCard:
    def __init__(self, data: dict):
        self.name = data.get("角色名字", "").strip()
        self.char_tag = data.get("角色tag", "").strip()
        self.body = data.get("角色体形", "").strip()
        self.face = data.get("角色面部", "").strip()
        self.outfits = data.get("角色衣服", {})  # {服装名: tags}
        self.personality = (data.get("角色性格") or "").strip()

    @property
    def identity_tags(self) -> str:
        """固定身份 tag：角色tag + 体形 + 面部（永远原样注入）"""
        parts = [p for p in (self.char_tag, self.body, self.face) if p]
        return ", ".join(parts)

    def rp_prompt(self, include_appearance: bool = True) -> str:
        """LLM 可读的角色扮演提示块（名字 + 性格 + 可选外貌简述）。"""
        lines = [f"角色：{self.name}"]
        if include_appearance and self.identity_tags:
            lines.append(f"外貌：{self.identity_tags}")
        if self.personality:
            block = self.personality if self.personality.startswith("性格") else f"性格：\n{self.personality}"
            lines.append(block)
        return "\n".join(lines)

    def outfit_tags(self, outfit: str | None = None) -> str:
        if not self.outfits:
            return ""
        if outfit is None:
            return next(iter(self.outfits.values()))
        if outfit in self.outfits:
            return self.outfits[outfit]
        raise KeyError(f"角色 {self.name} 没有服装 '{outfit}'，可选: {list(self.outfits)}")

    def list_outfits(self) -> list[str]:
        return list(self.outfits)

    def __repr__(self) -> str:
        return f"<CharCard {self.name} outfits={list(self.outfits)}>"


def list_characters(char_dir: Path = CHAR_DIR) -> list[str]:
    return sorted(p.stem for p in char_dir.glob("*.md") if p.stem != "README")


def load_character(name: str, char_dir: Path = CHAR_DIR) -> CharCard:
    """按角色名（文件名 stem）加载角色卡。"""
    path = char_dir / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"角色卡不存在: {path}（可用角色: {list_characters(char_dir)}）")
    return parse_card(path.read_text(encoding="utf-8"), path.stem)


def parse_card(text: str, default_name: str = "") -> CharCard:
    data: dict = {"角色名字": default_name, "角色tag": "", "角色体形": "", "角色面部": "", "角色衣服": {}, "角色性格": ""}
    current_key: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("---"):
            continue
        # 形如 "角色xxx：" 的字段行
        matched = False
        for key in KEYS:
            if line.startswith(key + "："):
                val = line[len(key) + 1 :].strip()
                if key == "角色衣服":
                    data[key] = {}  # 下面由列表项填充
                else:
                    data[key] = val
                current_key = key
                matched = True
                break
        if matched:
            continue
        # 服装列表项 "- 服装名: tags"
        if line.startswith("- "):
            item = line[2:].strip()
            if ":" in item:
                outfit_name, tags = item.split(":", 1)
                data.setdefault("角色衣服", {})[outfit_name.strip()] = tags.strip()
            elif current_key == "角色衣服":
                data.setdefault("角色衣服", {})[f"outfit{len(data['角色衣服'])+1}"] = item
            continue
        # 其他行：续行。自由文本字段按换行连接，tag 字段按逗号连接
        if current_key and current_key != "角色衣服":
            existing = data.get(current_key, "")
            if existing:
                joiner = "\n" if current_key in FREE_TEXT else ", "
                data[current_key] = existing + joiner + line
            else:
                data[current_key] = line
    if not data["角色衣服"]:
        data["角色衣服"] = {}
    return CharCard(data)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rp":
        name = sys.argv[2] if len(sys.argv) > 2 else "龙娘"
        card = load_character(name)
        print(card.rp_prompt())
        sys.exit(0)

    name = sys.argv[1] if len(sys.argv) > 1 else "龙娘"
    c = load_character(name)
    print(c)
    print("identity:", c.identity_tags)
    print("outfits :", c.list_outfits())
    for o in c.list_outfits():
        print(f"  - {o}: {c.outfit_tags(o)}")
    print("personality:")
    print(c.personality)
