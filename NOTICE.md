# NOTICE — 第三方数据与版权声明

## 一、Danbooru 标签数据（tagsearch/data/tags_enhanced.csv）

- **数据源**：[SAkizuki/DanbooruSearchOnlineDB](https://huggingface.co/datasets/SAkizuki/DanbooruSearchOnlineDB)（Hugging Face 数据集）及其配套仓库 [SuzumiyaAkizuki/DanbooruSearchOnline](https://github.com/SuzumiyaAkizuki/DanbooruSearchOnline) 的 `origin_database/tags_enhanced.csv`
- **许可**：**GPL-3.0**。完整许可文本见同目录 `tagsearch/data/LICENSE`（[在线版本](https://www.gnu.org/licenses/gpl-3.0.html)）
- **说明**：该数据由原作者通过 Danbooru API 抓取，并经 LLM 辅助中文翻译与语义扩充；仅收录 Danbooru 频数 ≥100 的 General / Character / Copyright 标签
- **分发**：本包内的该数据文件以 GPL-3.0 条款分发；引用时请保留本声明

## 二、派生数据

- 向量索引（`tagsearch/index/`、`settings_rag/index/`）为运行时由本机向量服务生成的派生数据，**不随本包分发**；若另行分发，须遵循其数据来源（GPL-3.0）条款

## 三、本项目自有代码

- 本仓库中除第三方数据外的代码与文档，以 **MIT License** 发布（见仓库根目录 `LICENSE`）；版权归项目所有者所有。
- 数据文件（`tagsearch/data/tags_enhanced.csv`）除外，仍按 GPL-3.0 分发（见第一节与 `tagsearch/data/LICENSE`）。

## 四、引用但不分发

- 本工具运行所依赖的外部组件（DeepSeek Harness、Forge Neo、LM Studio / Ollama、Anima 模型等）仅作链接指引与配置说明，**不在本包内分发**，各自版权归其作者所有
- 本包不含任何用户个人设定、角色卡、生成图片或本机环境配置（`config.json` 除外例化文件 `config.example.json`）
