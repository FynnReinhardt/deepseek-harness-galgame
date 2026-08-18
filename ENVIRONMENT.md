# 环境需求（初始化时由 DSH 读取）

> DSH 在初始化阶段读取本文件，按序检测并补齐环境。全部为本机部署，无云依赖。

## 一、必需

### 1. Python（含 numpy）

- Python 3.11+（Windows：从 [python.org](https://www.python.org/downloads/) 安装，勾选 *Add to PATH*）
- numpy：`pip install numpy`（直连失败用镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple`）

### 2. 向量服务（嵌入，**二选一即可**）

> LM Studio 与 Ollama 都是用来跑向量嵌入模型的，**两者选一即可**；
> **如果用户两者都没有 → 推荐安装 Ollama**（更轻量，纯命令行）。

| 方案 | 步骤 | config.json 指向 |
|---|---|---|
| **LM Studio**（图形化） | 安装 LM Studio → 加载嵌入模型 `bge-m3` 或 `nomic-embed-text-v1.5` | `embedding_url: http://127.0.0.1:1234/v1/embeddings`，`embedding_model: text-embedding-bge-m3` |
| **Ollama**（更轻量，**推荐兜底**） | ① `winget install Ollama.Ollama` ② `ollama pull bge-m3` ③ `ollama serve` | `backend: ollama`，`embedding_url: http://127.0.0.1:11434/v1/embeddings`，`embedding_model: bge-m3` |

> 二者 API 均为 OpenAI 兼容 `/v1/embeddings`，脚本自动按 `config.json` 切换，无需改代码。

## 二、绘画（可选——出立绘才需要）

### 1. Forge Neo（WebUI 后端）

```powershell
git clone https://github.com/Haoming02/sd-webui-forge-classic sd-webui-forge-neo --branch neo
```

启动时需附加 `--api` 参数（开放 `/sdapi/v1/*` 图像生成 API）。

### 2. 绘画模型（不强装，按用户喜好）

- 按个人偏好去 [civitai.red](https://civitai.red/) / [Hugging Face](https://huggingface.co/) 检索选用；
- **无特殊要求 → 基础版 Anima**（官方仓库 [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima)）：

| 文件 | 用途 | 下载（`resolve/main/split_files/...`） | 放置位置 |
|---|---|---|---|
| `anima-base-v1.0.safetensors` | 检查点（UNet） | `diffusion_models/anima-base-v1.0.safetensors` | `models/Stable-diffusion/` |
| `qwen_3_06b_base.safetensors` | **Text Encoder** | `text_encoders/qwen_3_06b_base.safetensors` | `models/text_encoder/` |
| `qwen_image_vae.safetensors` | VAE | `vae/qwen_image_vae.safetensors` | `models/VAE/` |

其他检查点版本：`anima-aesthetic-v1.1`（美学向）、`anima-turbo-v1.0`（快速出图）。

## 三、配置

- 无 `config.json` 时：复制 `config.example.json` 为 `config.json`，按下表填写
- 关键字段：
  - `webui_url`：Forge Neo 地址（默认 `http://127.0.0.1:7860`）
  - `backend` / `embedding_url` / `embedding_model`：向量服务（见上表）
  - `anima_text_encoder` / `anima_vae`：上述 Text Encoder / VAE 文件的**绝对路径**
  - `output_dir`：立绘输出目录（默认 `outputs/webui`）

## 四、验证

```powershell
python setup/detect_env.py
```

逐项输出 ✅/❌ + 缺失建议；全部 ✅ 即可进入下一步（导入设定库 → 建角色卡 → 切换人格）。
