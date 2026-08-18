# 插件源码（DSH 会话内动态插件）

本目录存放两个 **DeepSeek Harness 动态 Cordis 插件**的源码，**随部署包分发**（克隆即含），由 DSH 在初始化流程第 5 步（改造 DSH）部署。
（动态插件只存在于会话进程内，重启后需重新部署——因此源码随仓库分发，按本说明随时重建。）

## 前提

- **切换到「创造模式」**：动态插件的定义与运行依赖 `cordis_define` / `cordis_run` 工具，仅在创造模式（具备 Cordis 动态插件能力的会话）可用。若当前会话不是创造模式，先切换再继续。

## 插件列表

| 文件 | 插件（建议 idPrefix） | 作用 |
|---|---|---|
| `standing-panel.host.js` + `standing-panel.client.js` | 立绘侧栏（`stand`） | 右侧 details 列展示 `outputs/webui` 最新立绘，8 秒自动刷新，会话头部加"立绘"按钮 |
| `set-persona.host.js` | 人格切换（`pers`） | 注册 `set_persona` 工具：按角色卡（`characters/<名>.md`）把 DSH 人格切换为指定角色 / 恢复默认 |

## 激活步骤（在 DSH 会话内执行）

1. **替换占位符**（关键）：用 edit 工具把两个 host 文件里的 `__WORKSPACE__` 替换为**当前工作区的绝对路径**（如 `E:\xxx\deepseek-harness-galgame`）。插件据此读取 `<工作区>/config.json` 的 `output_dir` / `char_dir` 定位目录。
2. 用 read 工具读取对应 `.js` 文件（内容即 `code.host` / `code.client` 的函数体）。
3. `cordis_define`：
   - **立绘侧栏**：`plugin: { kind: "new", idPrefix: "stand" }`；`code.host` = `standing-panel.host.js` 内容，`code.client` = `standing-panel.client.js` 内容
   - **人格切换**：`plugin: { kind: "new", idPrefix: "pers" }`；`code.host` = `set-persona.host.js` 内容（无 Client）
4. `cordis_run` 运行对应 Package（Client 部分需用户在界面批准）。
5. 验证：右侧出现立绘面板（会话头部有"立绘"按钮）；工具列表出现 `set_persona`。

## 路径说明

- 插件运行时只依赖**定义时写入的工作区绝对路径** + 该工作区 `config.json` 的 `output_dir` / `char_dir`（配置项为绝对路径则直接用，相对路径则拼在工作区下）
- `config.json` 缺失时回退 `<工作区>/outputs/webui` / `<工作区>/characters`
- 不要依赖会话工作区推断（`sandboxPolicy.workspaceRoot` 绑定会话而非仓库位置）
