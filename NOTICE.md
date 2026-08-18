# NOTICE — 第三方数据与版权

## Danbooru 标签数据（tagsearch/data/tags_enhanced.csv）

- 来源：[SAkizuki/DanbooruSearchOnline](https://github.com/SuzumiyaAkizuki/DanbooruSearchOnline) 的 `origin_database/tags_enhanced.csv`
- 许可：**GPL-3.0**（[https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)）
- 说明：该数据由作者通过 Danbooru API 抓取，并经 LLM 辅助中文翻译与语义扩充；
  仅收录 Danbooru 频数 ≥100 的 General/Character/Copyright 标签。
- 本包内该数据文件以 GPL-3.0 条款分发；本工具其余代码与脚本为本项目自有。

## 其他

- 向量索引（tagsearch/index、settings_rag/index）为运行时由本机向量服务生成的派生数据，不随包分发。
- 本包不含任何用户个人设定、角色卡、生成图片或本机环境配置（config.json 除外例化文件）。
