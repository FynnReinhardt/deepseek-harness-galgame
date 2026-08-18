# tagsearch — 轻量 Danbooru 标签语义搜索（本地）

把自然语言（中/英）描述转成 Danbooru 标准 tag，供 A1111/Forge WebUI 出图用。**零重型依赖**：只用系统 python + numpy + 本机 LM Studio（bge-m3 嵌入）。

## 数据与版权

- 数据源：`data/tags_enhanced.csv`（52,476 条，Danbooru 频数 ≥100 的 General/Character/Copyright 标签；来自 [SAkizuki/DanbooruSearchOnline](https://github.com/SuzumiyaAkizuki/DanbooruSearchOnline) 的 origin_database，GPL-3.0，中文翻译/维基释义由作者 LLM 辅助生成）
- 原 CSV 为 GB18030 编码，已转存 UTF-8

## 组件

| 文件 | 作用 |
|---|---|
| `build_index.py` | 用 LM Studio bge-m3 把 52K 标签编码成两路向量（en=`name, wiki` / cn=`cn_name`），存 `index/`（float16，~220MB） |
| `search.py` | CLI 查询：自然语言 → top-k 标签（英文层 0.6 + 中文层 0.4 + 热度加成 0.15） |
| `server.py` | REST API（stdlib http.server，零依赖）：`GET /api/search?q=...` |

## 使用

```powershell
# 1) 构建索引（一次性，~18 分钟，需 LM Studio 在 1234 端口运行 bge-m3）
python build_index.py

# 2) CLI 查询
python search.py "穿着白色水手服的少女在雨中奔跑" --limit 20
python search.py "金发双马尾" --category 0 --nsfw

# 3) REST 服务（供其他程序/Agent 调用）
python server.py --port 8100
#    GET http://127.0.0.1:8100/api/search?q=白水手服少女&limit=30&nsfw=0
#    -> {"query":..., "prompt":"short_dress, rain, ..., white_serafuku", "results":[...]}
```

## 参数

- 查询权重：`EN_W=0.6`（英文层）、`POP_W=0.15`（热度加成，log 归一化）
- `category`：0=General、1=Character、2=Copyright
- 默认过滤 NSFW；`nsfw=1` 才显示

## 限制与后续

- 单层双路语义（原版是四路向量+共现推荐+画师推荐+工作区 UI），对大部分画面描述够用
- 后续可增量：共现推荐（`cooccurrence_clean.parquet` 已在本机 research/repos）、MCP 接口、分词
