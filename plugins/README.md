# 插件源码（DSH 会话内动态插件）

本目录存放两个 **DeepSeek Harness 动态 Cordis 插件**的源码，供新工作区的 DSH 会话定义并运行。
（动态插件只存在于会话进程内，重启后需重新定义——因此源码随仓库分发。）

## 插件列表

| 文件 | 插件（建议 idPrefix） | 作用 |
|---|---|---|
| `standing-panel.host.js` + `standing-panel.client.js` | 立绘侧栏（`stand`） | 右侧 details 列展示 `outputs/webui` 最新立绘，8 秒自动刷新，会话头部加"立绘"按钮 |
| `set-persona.host.js` | 人格切换（`pers`） | 注册 `set_persona` 工具：按角色卡（`characters/<名>.md`）把 DSH 人格切换为指定角色 / 恢复默认 |

## 激活步骤（在 DSH 会话内执行）

1. 用 read 工具读取对应 `.js` 文件（内容即 `code.host` / `code.client` 的函数体）
2. `cordis_define`：
   - **立绘侧栏**：`plugin: { kind: "new", idPrefix: "stand" }`；`code.host` = `standing-panel.host.js` 内容，`code.client` = `standing-panel.client.js` 内容
   - **人格切换**：`plugin: { kind: "new", idPrefix: "pers" }`；`code.host` = `set-persona.host.js` 内容（无 Client）
3. `cordis_run` 运行对应 Package（Client 部分需用户在界面批准）
4. 验证：右侧出现立绘面板（会话头部有"立绘"按钮）；工具列表出现 `set_persona`

## 路径说明

- 插件通过工作区根的 `config.json` 定位目录：立绘侧栏读 `output_dir`，人格切换读 `char_dir`
- 基准路径取自 `sandboxPolicy.workspaceRoot`；读不到 `config.json` 时回退相对路径（`outputs/webui` / `characters`）
- 若部署目录特殊，可在定义前用 edit 修改文件中的回退路径常量
