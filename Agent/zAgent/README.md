# zAgent

在 `Agent/Practice02/chat-stream-tool-fileOps.py` 基础上重构的智能体项目，按软件工程规范实现 **core 业务层与前端界面层分离**，当前提供 Textual TUI 终端界面，未来可扩展 web、desktop、mobile 等前端。

## 项目结构

```
zAgent/
├── core/            # 业务逻辑层，不依赖任何界面实现
│   ├── config.py    # 从 config.ini 加载 LLM 接口配置
│   ├── tools.py     # 10 个本地文件操作工具的注册表与实现
│   └── agent.py     # Agent 类：LLM 客户端与 function call 循环
├── tui/             # TUI 前端，Textual 终端聊天界面
│   └── app.py       # ChatTUI 应用，只调用 core.Agent 的接口
├── main.py          # 程序入口，选择使用哪个前端
├── config.ini       # LLM 接口配置，已被 .gitignore 排除
└── requirements.txt # 依赖：openai、textual
```

新增 web、desktop、mobile 前端时，与 `tui` 平级创建目录，复用 `core` 全部业务代码，入口处替换前端调用即可。

## 快速开始

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python main.py
```

`config.ini` 配置说明：

```ini
[LLM]
api_key = your_api_key_here
base_url = https://api.deepseek.com/v1
model = deepseek-chat
```

## 10 个文件操作工具

| 工具 | 功能 |
| --- | --- |
| getCWD | 获取当前工作目录 |
| listDirectory | 列出指定目录下所有文件和子目录 |
| getFileType | 获取指定文件的文件类型 |
| getFileContent | 获取指定文件的内容，仅支持纯文本 |
| createFile | 根据目录和文件名创建新文件 |
| editFile | 编辑指定文件的内容，仅支持纯文本 |
| createDirectory | 创建新目录 |
| deleteDirectory | 删除目录，支持非空目录 |
| deleteFile | 删除文件 |
| renameFileOrDir | 重命名文件和目录 |

## 架构说明

- core 层不导入任何 UI 组件，UI 层只调用 core 的公开接口，单向依赖。
- Agent 类内部维护会话上下文，执行 function call 循环：请求模型、执行工具、结果回传、递归至得到最终回答。
- 前端切换只需替换 `main.py` 中的前端入口，业务代码零改动。
