# AGENTS.md — deepseek-harness-galgame（DSH 插件：写小说/角色扮演自动生成立绘）

> 本工作区是 **DeepSeek Harness（DSH）的扩展插件**。写作 / 角色扮演 / 人格切换都在 DSH 会话中完成；
> 脚本只负责机械环节（环境检测、导入向量化、立绘出图、归档）。

## 初始化流程（新工作区首次打开时执行）

1. **环境检测与部署**
   - 运行 `python setup/detect_env.py`，按报告补齐缺失组件：
     - Python / numpy：`pip install numpy`（镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`）
     - 向量服务（二选一）：LM Studio（图形化）或 **Ollama（更轻）**：`winget install Ollama.Ollama` → `ollama pull bge-m3` → `ollama serve`，并把 `config.json` 的 `backend/embedding_url/embedding_model` 指向它
     - 绘画 WebUI（Forge Neo）：`git clone https://github.com/Haoming02/sd-webui-forge-classic sd-webui-forge-neo --branch neo`，启动加 `--api`；模型不强装，无特殊要求用基础版 Anima（配 Qwen Text Encoder+VAE，路径填入 `config.json` 的 `anima_text_encoder/anima_vae`）
   - 若无 `config.json`：复制 `config.example.json` 为 `config.json`，按其提示修改

2. **导入设定库**（用户把素材放入 `import/` 或提供文件路径后，由你执行）
   - `python settings_rag/import_docs.py` → 整理为 md → `library/` → 自动重建向量索引
   - `python settings_rag/retrieve.py "<查询>" --topk 3` 验证召回，把示例结果汇报给用户

3. **建角色卡**（用户描述角色，由你提取特征生成）
   - 按 `characters/README.md` 格式生成 `characters/<角色名>.md`（角色名字 / tag / 体形 / 面部 / 衣服多套 / 性格）
   - `python characters/validate.py <角色名>` 校验；展示卡片、按用户意见修改后锁定

4. **切换人格**（RP 开始 / 结束）
   - 确认 `set_persona` 插件可用；RP 开始调用 `set_persona { action: "set", char: "<角色名>" }`，结束调用 `{ action: "clear" }`
   - 立绘：`python pipeline/generate.py --char <角色名> --pov --scene-en "英文场景描述"`（后台运行，完成后告知图片路径）

## 日常流程

- **RP 参考**：`python pipeline/rp_ref.py --char <角色名> --query "<剧情要点>" --scene "<当前场景>"` → 角色卡性格 + 设定/小说向量召回
- **立绘提示词规则**：质量词 + 身份 tag + 服装 + `[pov, solo focus]` + 英文自然语言场景（详见 `skill/webui/prompt_rules.md`）
- **冒险历史归档**：段落结束后 `python settings_rag/archive_adventure.py --title "<段落标题>" --file <内容文件>` → 自动重建索引
- 完整流程见 `WORKFLOWS.md`；初始化手册见 `setup/README.md`

## 目录速查

| 目录 | 用途 |
|---|---|
| `import/` | 原始素材导入区（放这里由你导入） |
| `library/` | 整理后的设定/小说 + 冒险历史 |
| `characters/` | 角色卡（绘画 tag + RP 性格） |
| `tagsearch/` | Danbooru 语义标签搜索（自然语言 → 绘画 tag） |
| `settings_rag/` | 向量化 / 检索 / 冒险历史归档 |
| `pipeline/` | 立绘生成、RP 参考组装、角色卡解析 |
| `setup/` | 初始化系统：环境检测、工作区初始化、引导手册 |
| `skill/webui/` | DSH 绘画技能（WebUI 调用与提示词规则） |
| `config.json` | 环境配置（WebUI / 向量服务 / Anima 模型路径） |

## 注意事项

- **输出乱码**：脚本管道前设 `$env:PYTHONIOENCODING='utf-8'`（Windows GBK 控制台）
- **网络**：GitHub / Hugging Face 连接不稳时走代理（如 `git -c http.proxy=http://127.0.0.1:7897 push`）或切换代理节点
- **RP 节奏**：立绘先在后台生成（WebUI 出图约 25-40s），同时输出 RP 段落，出图完成即告知路径
- **数据版权**：`tagsearch/data/tags_enhanced.csv` 来自 SAkizuki/DanbooruSearchOnlineDB（GPL-3.0），见 `NOTICE.md`
