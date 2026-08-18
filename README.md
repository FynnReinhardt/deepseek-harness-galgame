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
- 向量服务：LM Studio（图形化）或 Ollama（更轻，`ollama pull bge-m3`）
- 绘画：Forge Neo（`git clone https://github.com/Haoming02/sd-webui-forge-classic sd-webui-forge-neo --branch neo`，加 `--api` 启动）
  模型不强装：按喜好去 civitai.red / Hugging Face 检索；无特殊要求用基础版 Anima（需配 Qwen CLIP+VAE，路径填进 config.json）

> 第三方数据版权见 NOTICE.md。
