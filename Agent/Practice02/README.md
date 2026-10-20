# chat-stream-tool-fileOps.py

一个**多轮对话 + Function Call（工具调用）**的命令行 AI 助手示例。
在 `chat-stream-tool-isLeapYear.py` 的基础上扩展，新增 **10 个本地文件操作工具**，
让模型真正"读写"本地磁盘，而不是编造文件操作结果。

- 架构图：[`chat-stream-tool-fileOps.mmd`](./chat-stream-tool-fileOps.mmd)（Mermaid 格式）
- 运行入口：`chat-stream-tool-fileOps.py`

---

## 一、快速开始

### 1. 环境依赖

```bash
pip install openai
```

- Python 3.7+
- 需要可用的 OpenAI 兼容接口（OpenAI / DeepSeek / 其他兼容 `tools` 的网关）

### 2. 配置 `config.ini`

脚本会从**与脚本同目录**的 `config.ini` 读取配置（`BASE_DIR` 由 `__file__` 推导）：

```ini
[LLM]
api_key = your_api_key_here
base_url = https://api.openai.com/v1
model = gpt-3.5-turbo
```

| 配置项 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `api_key` | **必填** | 无 | 为空会抛出 `ValueError` 并退出 |
| `base_url` | 可选 | `https://api.openai.com/v1` | 接口地址 |
| `model` | 可选 | `gpt-3.5-turbo` | 模型名，必须支持 `tools` 参数 |

### 3. 运行

```bash
python chat-stream-tool-fileOps.py
```

交互示例：

```text
欢迎使用带本地文件操作工具的多轮对话，输入 exit 或 quit 退出。

User: 看看当前目录有什么文件
Assistant: 当前目录下有 ... 文件 ...

User: 新建一个 note.txt，内容写个 hello
Assistant: 已为你创建 note.txt，内容为 hello。

User: exit
再见，期待下次与你对话！
```

输入 `exit` / `quit`（不区分大小写）或按 `Ctrl+C` 退出。

---

## 二、代码架构

### 1. 分层结构

```text
① 程序入口层        main() / __main__ / KeyboardInterrupt 兜底
② 配置加载层        load_config()  →  config.ini
③ LLM 客户端层      OpenAI client + client_kwargs["model"]
④ 多轮对话循环      input → 组装 messages → chat_with_tools → 打印回复
⑤ Function Call 引擎 chat_with_tools()（递归回传工具结果）
⑥ 工具注册表        TOOLS（JSON Schema）+ _params()
⑦ 工具实现层        10 个本地文件操作函数
⑧ 常量与数据        路径/超时/窗口/扩展名映射/会话历史
⑨ 本地文件系统      os / shutil
```

完整架构图见 `chat-stream-tool-fileOps.mmd`，可用 VS Code（Markdown Preview Mermaid 插件）、
Typora 或 <https://mermaid.live> 渲染。

### 2. 关键调用链

```text
main()
 ├─ load_config()                       # 读取并校验 config.ini
 ├─ OpenAI(api_key, base_url, timeout=60)
 ├─ messages = [system 提示词]
 └─ while True
     ├─ input() → 空输入跳过 / exit|quit 退出
     ├─ messages.append(user)
     ├─ trim_messages()                 # 裁剪至 MAX_MESSAGES=30 条
     ├─ chat_with_tools(client, messages)
     │   ├─ client.chat.completions.create(model, messages, tools=TOOLS)
     │   ├─ 若 msg.tool_calls 非空：
     │   │   ├─ append assistant（含 tool_calls 列表）
     │   │   ├─ 逐个 json.loads(arguments) → call_tool(name, args)
     │   │   ├─ append {"role": "tool", "tool_call_id", "content": result}
     │   │   └─ 递归 chat_with_tools()  ← 把结果回传模型，直到不再需要工具
     │   └─ 否则 return msg.content
     └─ messages.append(assistant) → 打印回复
```

要点：

- **工具结果回传**：工具执行完后必须作为 `role=tool` 消息追加，带上 `tool_call_id`，
  再递归请求模型，模型才能基于真实结果作答。
- **递归而非循环**：`chat_with_tools()` 使用递归实现"多轮工具调用"，可在一次提问中连续调用多个工具。
- **上下文窗口**：`trim_messages()` 从索引 1 起删除（`messages[1:1+excess]`），
  保留 `system` 提示词不被裁掉。
- **异常处理**：请求失败时 `messages.pop()` 回滚本条用户消息，避免污染上下文。

---

## 三、工具清单（10 个）

注册在 `TOOLS` 中，由 `call_tool()` 按名称分发：

| 工具名 | 实现函数 | 主要参数 | 说明 |
| --- | --- | --- | --- |
| `getCWD` | `get_cwd()` | — | 获取当前工作目录 |
| `listDirectory` | `list_directory()` | `path`（默认 `.`） | 列出目录下文件/子目录 |
| `getFileType` | `get_file_type()` | `path` | 按扩展名映射到 `FILE_TYPES` 描述 |
| `getFileContent` | `get_file_content()` | `path` | 读取纯文本（UTF-8），二进制类型拒绝 |
| `createFile` | `create_file()` | `directory`, `filename`, `content` | 目录不存在自动创建；文件已存在则拒绝 |
| `editFile` | `edit_file()` | `path`, `content` | 覆盖写入，仅限已存在的文件 |
| `createDirectory` | `create_directory()` | `path` | `makedirs(exist_ok=True)` |
| `deleteDirectory` | `delete_directory()` | `path` | `shutil.rmtree`，**支持非空目录** |
| `deleteFile` | `delete_file()` | `path` | `os.remove` |
| `renameFileOrDir` | `rename_file_or_dir()` | `old_path`, `new_path` | 目标已存在时拒绝 |

`_params(properties, required)` 是一个小工具函数，用于生成 OpenAI 标准的
`{"type": "object", "properties": {...}, "required": [...]}` 参数 Schema。

---

## 四、全局常量

| 常量 | 值 | 作用 |
| --- | --- | --- |
| `BASE_DIR` | 脚本所在目录 | 定位 `config.ini` |
| `CONFIG_FILE` | `BASE_DIR/config.ini` | 配置文件路径 |
| `DEFAULT_TIMEOUT` | `60` | 客户端超时（秒） |
| `DEFAULT_BASE_URL` | `https://api.openai.com/v1` | 默认接口地址 |
| `DEFAULT_MODEL` | `gpt-3.5-turbo` | 默认模型 |
| `MAX_MESSAGES` | `30` | 上下文消息条数上限 |
| `EXIT_WORDS` | `("exit", "quit")` | 退出指令 |
| `FILE_TYPES` | 扩展名 → 类型描述 | 判断文件类型 / 是否可读文本 |

---

## 五、安全提示 ⚠️

- 工具具备**真实写入、删除、重命名**能力，`deleteDirectory` 会**递归删除非空目录**，
  请勿在重要目录下随意运行。
- 删除/重命名类工具**没有二次确认**，建议在实际使用前自行加入人工确认或路径白名单。
- `config.ini` 中含明文 API Key，请勿提交到公开仓库（建议加入 `.gitignore`）。
- `createFile` 会把 AI 生成的任意文本落盘，注意内容审计。

---

## 六、已知限制

- `getFileContent` / `editFile` 只支持 UTF-8 纯文本，其他编码会返回错误提示。
- `editFile` 是**整体覆盖**写入，不支持局部替换 / 差分编辑。
- 上下文裁剪是"从头丢弃最早消息"的简单策略，长对话可能丢失早期上下文。
- `chat_with_tools()` 递归层数取决于模型行为，未设置递归上限保护。

---

## 七、同目录其他示例

| 文件 | 说明 |
| --- | --- |
| `chat-stream-tool-getDate.py` | 日期类工具调用示例 |
| `chat-stream-tool-isLeapYear.py` | 闰年判断工具示例（本脚本的前身） |
| `config.ini` | LLM 接口配置 |
