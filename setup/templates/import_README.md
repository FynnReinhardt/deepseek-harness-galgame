# import/ — 原始素材导入区

把要挂载为角色扮演参考的**设定集 / 小说**原始素材放到这里，然后运行：

```powershell
python settings_rag/import_docs.py
```

## 流程

```
import/ 原始素材（单个文件 或 .zip 压缩包）
  → 整理为 markdown（UTF-8）
  → 输出到 library/（独立目录，zip 保留内部目录结构）
  → 自动重建向量索引（settings_rag/index/）
  → RP 时随时检索参考
```

## 支持的格式

| 格式 | 说明 |
|---|---|
| `.md` / `.txt` | 直接整理（自动转 UTF-8，兼容 GB18030） |
| `.docx` | 内置 zip 解析转 md，保留标题层级，零依赖 |
| `.pdf` | 首次使用自动安装 pypdf |
| `.html` / `.htm` | 标签转 md（h1-h6 → #） |
| `.epub` | 解包转 md |
| `.zip` | 递归处理包内所有上述格式，保留目录结构 |

## 参数

```powershell
python settings_rag/import_docs.py --src 某目录    # 指定来源
python settings_rag/import_docs.py --force         # 覆盖 library/ 同名文件
python settings_rag/import_docs.py --no-build      # 只整理不重建索引
```
