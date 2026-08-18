# 角色卡格式规范（绘画 + 角色扮演双用途）

> 一张角色卡两个用途：
> - **绘画**：`角色tag/角色体形/角色面部/角色衣服` 在**建卡时固定**，出图时原样注入 → 角色形象跨场景一致；只有「角色衣服」可换。
> - **扮演**：`角色性格` 是自由文本，RP 时由 LLM 读取，决定角色的言行举止。

## 文件

- 每个角色一个 markdown 文件：`characters/<角色名>.md`，UTF-8 编码
- 角色名作为 `--char` 参数传入 `pipeline/generate.py`；RP 时直接读文件或 `python pipeline/characters.py --rp <角色名>`

## 字段

| 字段 | 必填 | 用途 | 说明 |
|---|---|---|---|
| `角色名字` | ✅ | 双用 | 显示名/索引名 |
| `角色tag` | 视情况 | 绘画 | **IP 角色**：Danbooru 库里已有的角色 tag（如 `frieren_(sousou_no_frieren)`）；**需 LoRA**：`<lora:xxx:0.8>`；原创留空 |
| `角色体形` | ✅ | 绘画 | 体型 + breast size：`petite` / `mature female` / 留空 / 用户指定 |
| `角色面部` | ✅ | 绘画 | 发型、头饰、兽耳/角、瞳色、换衣不换的配饰（泪痣、眼镜、项圈等） |
| `角色衣服` | ✅ | 绘画 | 多套服装 `- 服装名: tags`，出图用 `--outfit` 切换 |
| `角色性格` | RP | 扮演 | **自由文本**，按需分小节（性格/口头禅/说话方式/习惯/恐惧/目标…），LLM 扮演时直接读这段 |

## 绘画一致性规则（pipeline/generate.py 强制）

```
prompt = 质量词 + <角色tag> + <角色体形> + <角色面部> + <角色衣服[outfit]> + <场景 tags> + 背景词
```

- `角色tag/角色体形/角色面部` 固定顺序、固定内容，永不改变
- 场景 tags（动作/天气/构图）来自 tagsearch 语义检索，动态追加
- 负面词固定模板

## 特征 tag 生成（建卡时，参考本地 danbooru 库）

生成 `角色体形 / 角色面部 / 角色衣服` 的特征 tag 时，**逐条用本地向量化 danbooru 库验证/取标准 tag**：

```powershell
python tagsearch/search.py "银白色长发" --limit 5   # → silver_hair, long_hair ...
python tagsearch/search.py "水手服" --limit 5        # → serafuku ...
python tagsearch/search.py "狐耳" --limit 5          # → fox_ears ...
```

- 每条特征都应有本地库命中的标准 tag（避免自造 / 幻觉 tag），出图时这些 tag 与场景检索同源、保持一致
- 库中无对应 tag 的特殊特征：保留自定义写法并在卡中注明（或用 LoRA 兜底）

## RP 使用

```powershell
# 输出 LLM 可读的角色扮演提示块（名字 + 性格 + 可选外貌描述）
python pipeline/characters.py --rp 龙娘
```

扮演时把输出块注入 LLM 上下文，角色言行即按 `角色性格` 执行；出图时用同一张卡保证形象一致。

## 示例

见 `characters/龙娘.md`。
