# AGENTS.md — deepseek-harness-galgame（DSH 插件：写小说/角色扮演自动生成立绘）

> 本工作区是 **DeepSeek Harness（DSH）的扩展插件**。写作 / 角色扮演 / 人格切换都在 DSH 会话中完成；
> 脚本只负责机械环节（环境检测、导入向量化、立绘出图、归档）。

## 初始化流程（新工作区首次打开时执行）

1. **环境检测与部署**
   - 运行 `python setup/detect_env.py` 获取检测报告
   - **完整环境需求与部署命令见 `ENVIRONMENT.md`**：Python/numpy、向量服务二选一（LM Studio / Ollama）、Forge Neo 安装、Anima 模型 + Text Encoder + VAE 下载地址、`config.json` 字段说明——按需安装补齐
   - 若无 `config.json`：复制 `config.example.json` 为 `config.json`，按 `ENVIRONMENT.md` 第三节填写

2. **导入设定库**（用户把素材放入 `import/` 或提供文件路径后，由你执行）
   - `python settings_rag/import_docs.py` → 整理为 md → `library/` → 自动重建向量索引
   - `python settings_rag/retrieve.py "<查询>" --topk 3` 验证召回，把示例结果汇报给用户

3. **建角色卡**（用户描述角色，由你提取特征生成）
   - 按 `characters/README.md` 格式生成 `characters/<角色名>.md`（角色名字 / tag / 体形 / 面部 / 衣服多套 / 性格）
   - `python characters/validate.py <角色名>` 校验；展示卡片、按用户意见修改后锁定

4. **切换人格**（RP 开始 / 结束）
   - 使用第 5 步激活的 `set_persona` 工具；RP 开始调用 `set_persona { action: "set", char: "<角色名>" }`，结束调用 `{ action: "clear" }`
   - 立绘：`python pipeline/generate.py --char <角色名> --pov --scene-en "英文场景描述"`（后台运行，完成后告知图片路径）

5. **改造 DSH（激活动态插件）**
   - 本工具的立绘侧栏与人格切换依赖两个 DSH 动态 Cordis 插件（仅存在于会话进程，重启后需重新激活）：
     - **立绘侧栏**（右侧展示立绘 + 会话头部"立绘"按钮）：读取 `plugins/standing-panel.host.js` 与 `plugins/standing-panel.client.js`，用 `cordis_define`（kind=new, idPrefix=stand）定义后 `cordis_run` 运行（Client 需用户批准）
     - **人格切换**（`set_persona` 工具）：读取 `plugins/set-persona.host.js`，用 `cordis_define`（kind=new, idPrefix=pers）定义后 `cordis_run` 运行
   - 详细步骤见 `plugins/README.md`；插件通过工作区 `config.json` 的 `output_dir` / `char_dir` 定位目录

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
| `plugins/` | DSH 动态插件源码（立绘侧栏 / 人格切换），供会话激活 |
| `setup/` | 初始化系统：环境检测、工作区初始化、引导手册 |
| `skill/webui/` | DSH 绘画技能（WebUI 调用与提示词规则） |
| `config.json` | 环境配置（WebUI / 向量服务 / Anima 模型路径） |

## 注意事项

- **输出乱码**：脚本管道前设 `$env:PYTHONIOENCODING='utf-8'`（Windows GBK 控制台）
- **网络**：GitHub / Hugging Face 连接不稳时走代理（如 `git -c http.proxy=http://127.0.0.1:7897 push`）或切换代理节点
- **RP 节奏**：立绘先在后台生成（WebUI 出图约 25-40s），同时输出 RP 段落，出图完成即告知路径
- **数据版权**：`tagsearch/data/tags_enhanced.csv` 来自 SAkizuki/DanbooruSearchOnlineDB（GPL-3.0），见 `NOTICE.md`
