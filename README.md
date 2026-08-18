# AutoWebUI — 写小说/角色扮演自动生成立绘

把"设定库 + 角色卡 + 本地绘画"串成一条流水线：RP 时按剧情检索设定、自动生成角色立绘、DSH 人格切换扮演。

## 快速开始

```powershell
# 1. 一键安装（检测 python/numpy → 生成配置 → 环境检测 → 建标签索引）
.\install.ps1

# 2. 完整初始化引导（部署/环境/Ollama 兜底/导入/角色）
详见 setup\README.md

# 3. 日常流程（角色卡/立绘规则/RP 参考/冒险历史归档/人格切换）
详见 WORKFLOWS.md
```

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
- 绘画模型（可选）：本工具**不强制要求**安装任何特定模型。您可依照个人偏好，在 [civitai.red](https://civitai.red/) 或 [Hugging Face](https://huggingface.co/) 中检索并选用合适的模型；如无特别偏好，建议采用基础版 Anima 模型——该类模型需配套 Qwen CLIP 与 Qwen VAE 文件，并将对应文件路径填写至 `config.json` 的 `anima_clip` / `anima_vae` 字段。

## 数据来源声明

本工具内置的 Danbooru 标签检索数据（`tagsearch/data/tags_enhanced.csv`）源自开源项目 [SAkizuki/DanbooruSearchOnlineDB](https://huggingface.co/datasets/SAkizuki/DanbooruSearchOnlineDB)（Hugging Face 数据集）及其配套仓库 [SuzumiyaAkizuki/DanbooruSearchOnline](https://github.com/SuzumiyaAkizuki/DanbooruSearchOnline)，按 **GPL-3.0** 许可分发。完整声明见 `NOTICE.md`。
