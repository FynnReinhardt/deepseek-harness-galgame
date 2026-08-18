# 三流程固化说明书（Runbook）

> DSH 即写文宿主：**角色提取、扮演输出都由 DSH 会话完成**（不用本地 LLM）；
> 脚本只负责机械环节（写卡/归档/建索引/校验）。
> 约定编码：所有脚本前设 `$env:PYTHONIOENCODING='utf-8'`。

---

## 流程 1 · 角色创建（自动提取特征 → 角色卡 → 按意见修改）

**触发**：用户描述一个新角色（任意格式：一段文字/人设草稿/截图转述）。

**DSH 执行步骤**：
1. 从描述中提取以下字段（按 `characters/README.md` 规范）：
   - `角色名字`：名字/别名
   - `角色tag`：IP 角色 → Danbooru 角色 tag；需 LoRA → `<lora:xxx:0.8>`；原创留空
   - `角色体形`：体型 + breast size（petite / mature female / 留空 / 用户指定）
   - `角色面部`：发型、头饰、兽耳/角、瞳色、**换衣不换的配饰**（泪痣/眼镜/项圈…）
   - `角色衣服`：多套服装（`- 服装名: tags`），默认至少一套
   - `角色性格`：性格/口头禅/说话方式/习惯/恐惧/目标（自由文本，RP 用）
2. 写入 `characters/<角色名字>.md`（UTF-8）
3. 用 `characters/validate.py <名字>` 校验字段完整度
4. **展示卡片给用户 → 按用户意见修改 → 反复直到锁定**（锁定后身份 tag 不再变，保形象一致）

**命令**：
```powershell
python characters/validate.py          # 列出所有角色卡
python characters/validate.py 龙娘      # 校验单张卡
```

**产出**：`characters/<名字>.md`（绘画 + 扮演双用途）
- 出图：`python pipeline/generate.py --char <名字> --desc "场景" --outfit 服装名`
- 扮演：`python pipeline/characters.py --rp <名字>`

---

## 立绘提示词规则（Anima，2026-08-18 固化）

出图（`pipeline/generate.py`）遵循：

```
质量词 + 角色身份tag(卡) + 服装tag(卡) + [pov, solo focus]
+ 本地 danbooru 库锚点 tag（--tag-count，默认 10）
+ 英文自然语言场景描述
```

- 场景/动作/背景 → **英文自然语言一段**（`--scene-en`），不用动作类 tag
- **表情 → tag 库**（`--tags "blush, embarrassed"`，从本地 danbooru 库选，可多个）
- **肢体动作 → 英文自然语言 + 最多 1-2 个 tag**
- **本地向量化 danbooru 库始终参考**：无 `--tags` 时 NL 路径也会用 tagsearch 检索一批锚点 tag 拼在 NL 前；`--tag-count 0` 可关闭（纯 NL）
- 与主角互动 → `--pov`（加 pov, solo focus）；不互动不加
- 背景 tag 默认不加（`--simple-bg` 仅在场景不明确时）
- 负面词含防 Q 版：`chibi, deformed, oversized head, small head`
- 完整规则见 `skill/webui/prompt_rules.md`

---

## 流程 2 · 设定集导入 + RAG 参考

**触发**：有新设定/小说素材（单个文件或 zip）。

**命令**（一条到底）：
```powershell
python settings_rag/import_docs.py
# 支持: zip / txt / md / docx / pdf / html / epub
# 流程: import/ → 转 md → library/（保留结构）→ 重建向量索引
```

**RP 时检索参考**（每回合由 DSH 调用）：
```powershell
python pipeline/rp_ref.py --char <角色> --query "剧情要点" --scene "当前场景" [--topk 4]
# 输出: 角色卡性格 + 当前场景 + 设定/小说向量召回 → 注入 LLM 上下文
```

**维护**：
```powershell
python settings_rag/import_docs.py --force   # 覆盖同名
python settings_rag/import_docs.py --no-build # 只整理不建索引
python settings_rag/build_index.py            # 手动重建索引
```

---

## 流程 3 · 扮演段落归档为冒险历史

**触发**：扮演每到一个**段落结束**（一个事件/章节/自然断点）。

**DSH 执行步骤**：
1. 把该段扮演内容（对话 + 剧情推进）整理为文本
2. 归档：
```powershell
python settings_rag/archive_adventure.py --title "段落标题" --file rp_segment.txt
# 或直接传内容:
python settings_rag/archive_adventure.py --title "雨夜禁书区" --text "扮演内容..."
# 可加 --summary "一句话摘要"
```
3. 脚本自动：写入 `library/冒险历史/YYYYMMDD-HHMMSS-<标题>.md` → **重建向量索引**

**效果**：之后的 RP 通过 `rp_ref.py` 检索"发生过什么"，冒险历史成为长程记忆的一部分。

---

## 流程 4 · 人格切换（DSH 扮演用户主要角色）

**机制**：`set_persona` 工具（pers-2 插件）把角色卡（`characters/<名>.md`）注入 system prompt 的 `deployment:persona`（order 0），**替换 DSH 默认人格**；`clear` 恢复。

**DSH 用法**：
- RP 开始：调用 `set_persona { action: "set", char: "<角色名>" }`（如 龙娘/羽织/DS娘）
- 之后 DSH 以该角色身份扮演（性格/外貌来自角色卡）
- RP 结束：调用 `set_persona { action: "clear" }` 恢复默认人格

**注入内容**：`# 当前扮演人格 / 你正在扮演角色：X / 外貌：… / 性格：… / 【扮演指令】（贴合性格、设定以向量库为准、不跳出角色）`

**注意**：插件为会话内动态插件，进程重启后需重新 `cordis_run` 激活（`set_persona` 工具才会出现）。

---

## 目录总览

| 目录 | 内容 |
|---|---|
| `characters/` | 角色卡（固定 tag + 性格）+ `README.md` 格式规范 + `validate.py` |
| `settings/` `novels/` | 示例设定/小说（可删） |
| `library/` | 整理好的真实素材（`设定集/`）+ `冒险历史/` |
| `import/` | 原始素材导入区（zip/文档） |
| `settings_rag/` | 向量化（build/import/archive）+ 检索（retrieve） |
| `pipeline/` | 立绘生成（generate）、RP 参考组装（rp_ref）、角色卡解析（characters.py） |
| `tagsearch/` | Danbooru 语义标签搜索（自然语言→tag） |

## 依赖服务

- LM Studio `http://127.0.0.1:1234`：bge-m3 嵌入（向量化/检索）
- Forge Neo WebUI `http://127.0.0.1:7860`：Anima 模型出图（`--api`）
- 系统 python 3.14 + numpy（已装）
