# AutoWebUI — 写小说/角色扮演自动生成立绘

> **本工具是 [DeepSeek Harness](https://github.com/deepseek-ai/)（DSH）的扩展插件，依赖 DeepSeek Harness 运行。**
> 写作/角色扮演/人格切换均在 DSH 会话中进行：由 DSH 读取角色卡性格进行扮演、调用 `set_persona` 切换 DSH 自身人格、按剧情检索设定库、并在对话中触发立绘生成。

把"设定库 + 角色卡 + 本地绘画"串成一条流水线：RP 时按剧情检索设定、自动生成角色立绘、DSH 人格切换扮演。

## 快速开始

```powershell
# 1. 克隆项目
git clone https://github.com/FynnReinhardt/deepseek-harness-galgame

# 2. 在 DeepSeek Harness 中把克隆目录作为工作区打开

# 3. ⚠️ 切换到「创造模式」：初始化依赖 Cordis 动态插件能力（立绘侧栏、人格切换的
#    定义与运行需要 cordis_define / cordis_run 工具），请在 DSH 中切换到创造模式后再开始。

# 4. 告诉 DSH 开始初始化：它会读取 AGENTS.md 并自动执行
#      环境检测与部署 → 导入设定库（提供你喜欢的小说或者设定集的 txt 文档作为扮演的背景）
#      → 建角色卡 → 部署插件（立绘侧栏/人格切换）→ 开始扮演
#    详细步骤见 AGENTS.md；人工操作手册见 setup\README.md
```

**环境部署提示**：向量模型（嵌入服务）与绘画后端（Forge Neo + 模型）的检测、安装与配置，均可交由 **DeepSeek Harness 协助完成**——在 DSH 会话中运行 `python setup/detect_env.py` 获取检测报告，DSH 会按报告引导补齐缺失组件（向量服务二者选一：LM Studio 或 Ollama，均未安装时推荐 Ollama）。

## 组件

| 目录 | 用途 |
|---|---|
| `setup/` | 初始化系统：环境检测、工作区初始化、安装手册 |
| `tagsearch/` | Danbooru 语义标签搜索（自然语言 → 绘画 tag） |
| `settings_rag/` | 设定集/小说向量化 + 检索 + 冒险历史归档 |
| `pipeline/` | 立绘生成、RP 参考组装、角色卡解析 |
| `characters/` | 角色卡格式规范（用户角色卡由初始化后创建） |
| `skill/webui/` | DSH 绘画技能（WebUI 调用与提示词规则） |
| `config.json` | 环境配置（WebUI/向量服务/Anima 模型路径） |

## 依赖（二选一向量服务 + 可选绘画）

- Python 3.11+（numpy）
- 向量服务：LM Studio（图形化界面）或 Ollama（更轻量，`ollama pull bge-m3`）
- 绘画后端：**Forge Neo**。安装命令：`git clone https://github.com/Haoming02/sd-webui-forge-classic sd-webui-forge-neo --branch neo`；启动时需附加 `--api` 参数以开放图像生成 API。
- 绘画模型（可选）：本工具**不强制要求**安装任何特定模型。您可依照个人偏好，在 [civitai.red](https://civitai.red/) 或 [Hugging Face](https://huggingface.co/) 中检索并选用合适的模型；如无特别偏好，建议采用基础版 Anima 模型——该类模型需配套 Qwen Text Encoder 与 Qwen VAE 文件，并将对应文件路径填写至 `config.json` 的 `anima_text_encoder` / `anima_vae` 字段。下载地址见下方。

#### Anima 模型下载（官方仓库 [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima)）

| 文件 | 用途 | 下载地址（`resolve/main/...`） |
|---|---|---|
| `anima-base-v1.0.safetensors` | 基础版 Anima 检查点（无特殊要求时选它） | `https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/diffusion_models/anima-base-v1.0.safetensors` |
| `qwen_3_06b_base.safetensors` | Text Encoder（Qwen3 0.6B，即 CLIP） | `https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/text_encoders/qwen_3_06b_base.safetensors` |
| `qwen_image_vae.safetensors` | VAE | `https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/vae/qwen_image_vae.safetensors` |

其他检查点版本（`split_files/diffusion_models/` 下）：`anima-aesthetic-v1.1`（美学向）、`anima-turbo-v1.0`（快速出图）等。

**放置与配置**：
- 检查点 → Forge Neo 的 `models/Stable-diffusion/`
- Text Encoder → `models/text_encoder/`；VAE → `models/VAE/`
- 将后两者的路径填入 `config.json` 的 `anima_text_encoder` / `anima_vae`（Forge 经 `forge_additional_modules` 自动加载）

## 数据来源声明

本工具内置的 Danbooru 标签检索数据（`tagsearch/data/tags_enhanced.csv`）源自开源项目 [SAkizuki/DanbooruSearchOnlineDB](https://huggingface.co/datasets/SAkizuki/DanbooruSearchOnlineDB)（Hugging Face 数据集）及其配套仓库 [SuzumiyaAkizuki/DanbooruSearchOnline](https://github.com/SuzumiyaAkizuki/DanbooruSearchOnline)，按 **GPL-3.0** 许可分发。完整声明见 `NOTICE.md`。
