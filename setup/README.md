# 初始化指南（新工作区部署引导）

> 目标：把本工具部署到**新的工作区**并跑通"设定库 + 角色扮演 + 立绘"全流程。
> 全程由 DSH 会话引导执行；脚本只做机械环节。

---

## 第 1 步 · 部署到新工作区

```powershell
# 在目标目录（新工作区）初始化
python setup/init_workspace.py --dir D:\my-novel-project

# 或指定向量后端/WebUI 地址
python setup/init_workspace.py --dir D:\my-novel-project --backend ollama
python setup/init_workspace.py --dir D:\my-novel-project --webui-url http://127.0.0.1:7860
```

自动完成：
- 创建目录：`characters/ settings/ novels/ import/ library/ outputs/webui/ tagsearch/data/`
- 生成 `config.json`（自动检测 lmstudio / ollama）
- 复制模板：角色卡模板、格式规范、导入说明

> 若目标目录为空的新工作区，需先把本项目脚本（`setup/ settings_rag/ pipeline/ tagsearch/ characters/`）复制/克隆过去。

## 第 2 步 · 环境检测与部署

```powershell
python setup/detect_env.py
```

检测项与缺失处理：

| 缺失项 | 处理 |
|---|---|
| **Python / numpy** | `pip install numpy`（镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`） |
| **绘画 WebUI（Forge Neo）** | 安装脚本：<br> `git clone https://github.com/Haoming02/sd-webui-forge-classic sd-webui-forge-neo --branch neo`<br> 启动参数加 `--api` |
| **绘画模型（可选，不强装）** | 按用户喜好去 [civitai.red](https://civitai.red/) 与 [Hugging Face](https://huggingface.co/) 检索；**无特殊要求时下载基础版 Anima**（如 anima-base-1.0，在 HF/civitai.red 搜 "anima base"）。Anima 系需配套 Qwen CLIP（`qwen_3_06b_base.safetensors`）与 Qwen VAE（`qwen_image_vae.safetensors`），经 `override_settings.forge_additional_modules` 传入（见 `skill/webui/SKILL.md`） |
| **向量服务（LM Studio）** | 安装 LM Studio 并加载嵌入模型（`bge-m3` / `nomic-embed-text-v1.5`） |
| **向量服务（无 LM Studio）** | **安装 Ollama（更轻量简单）**：<br> ① `winget install Ollama.Ollama`<br> ② `ollama pull bge-m3`<br> ③ `ollama serve`<br> ④ 改 `config.json`：`backend: "ollama"`、`embedding_url: "http://127.0.0.1:11434/v1/embeddings"`、`embedding_model: "bge-m3"` |

> 向量服务二选一即可：LM Studio 图形化、Ollama 命令行更轻。`config.json` 的 `embedding_url/model` 指向谁就用谁，脚本全部走 OpenAI 兼容 `/v1/embeddings`。

## 第 3 步 · 导入设定集/小说并向量化（由 DSH 完成）

把素材（zip / txt / docx / pdf / html / epub）放进 `import/`（或在 DSH 会话中直接提供文件路径），然后告诉 DSH：「**素材已放好，导入设定库**」。

DSH 会代为执行并汇报结果：

```powershell
python settings_rag/import_docs.py            # 整理为 md → library/ → 自动重建向量索引
python settings_rag/retrieve.py "某角色/某设定" --topk 3   # 验证召回
```

> 你无需手动运行命令；导入完成、向量库就绪后，DSH 会给出检索示例供你确认。

## 第 4 步 · 提取角色 + 切换人格

1. **建角色卡**：DSH 根据你描述的角色提取特征生成 `characters/<角色名>.md`（或按 `characters/角色卡模板.md` 手动填写），用 `python characters/validate.py <角色名>` 校验
2. **切换人格**：在 DSH 会话中调用 `set_persona { action: "set", char: "<角色名>" }`（需先激活 pers-2 插件）；RP 结束调用 `set_persona { action: "clear" }`
3. **出立绘**：`python pipeline/generate.py --char <角色名> --pov --scene-en "英文场景描述"`

---

## 目录速查

| 目录 | 用途 |
|---|---|
| `import/` | 原始素材导入区（丢这里→自动整理） |
| `library/` | 整理好的设定/小说 + 冒险历史 |
| `characters/` | 角色卡（绘画 tag + RP 性格） |
| `settings/` `novels/` | 示例文档（可删） |
| `outputs/webui/` | 立绘输出 |
| `config.json` | 环境配置（WebUI/向量服务地址） |

详细流程见 `WORKFLOWS.md`（三流程 + 立绘规则 + 人格切换）。
