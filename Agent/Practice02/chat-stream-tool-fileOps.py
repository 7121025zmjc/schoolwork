# -*- coding: utf-8 -*-
"""
chat-stream-tool-fileOps.py —— 多轮对话 + function call 文件操作工具组
基于 chat-stream-tool-isLeapYear.py 开发，新增 10 个本地文件操作工具：
getCWD / listDirectory / getFileType / getFileContent / createFile /
editFile / createDirectory / deleteDirectory / deleteFile / renameFileOrDir
运行：python chat-stream-tool-fileOps.py
"""
import configparser
import json
import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")
DEFAULT_TIMEOUT = 60
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_MESSAGES = 30
EXIT_WORDS = ("exit", "quit")

# 常见扩展名 -> 文件类型说明
FILE_TYPES = {
    ".txt": "纯文本文件", ".md": "Markdown 文本文件", ".py": "Python 源文件",
    ".json": "JSON 数据文件", ".ini": "配置文件", ".csv": "CSV 表格文件",
    ".html": "HTML 网页文件", ".css": "CSS 样式文件", ".js": "JavaScript 源文件",
    ".png": "PNG 图片", ".jpg": "JPEG 图片", ".exe": "可执行程序",
    ".pdf": "PDF 文档", ".docx": "Word 文档", ".zip": "压缩包",
}


def load_config(path=CONFIG_FILE):
    if not os.path.exists(path):
        raise FileNotFoundError(
            "未找到配置文件 %s，请先参照以下格式创建：\n"
            "[LLM]\napi_key = your_api_key_here\n"
            "base_url = https://api.openai.com/v1\nmodel = gpt-3.5-turbo" % path)
    config = configparser.ConfigParser()
    try:
        config.read(path, encoding="utf-8")
    except (configparser.Error, UnicodeDecodeError) as e:
        raise ValueError("读取配置文件失败：%s" % e)
    if not config.has_section("LLM"):
        raise ValueError("配置文件中缺少 [LLM] 段，请检查 config.ini 格式。")
    api_key = config.get("LLM", "api_key", fallback="").strip()
    if not api_key:
        raise ValueError("配置文件中 api_key 为空，请填写有效的 API Key。")
    base_url = config.get("LLM", "base_url", fallback=DEFAULT_BASE_URL).strip()
    model = config.get("LLM", "model", fallback=DEFAULT_MODEL).strip()
    return {"api_key": api_key, "base_url": base_url, "model": model}


def trim_messages(messages):
    if len(messages) <= MAX_MESSAGES:
        return
    excess = len(messages) - MAX_MESSAGES
    del messages[1:1 + excess]


# ---------- 10 个本地文件操作工具 ----------

def get_cwd():
    """获取当前工作目录。"""
    return "当前工作目录：%s" % os.getcwd()


def list_directory(path="."):
    """列出指定目录下所有文件和子目录。"""
    if not os.path.isdir(path):
        return "错误：%s 不是有效目录" % path
    entries = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        kind = "目录" if os.path.isdir(full) else "文件"
        entries.append("%s %s" % (kind, name))
    if not entries:
        return "%s 目录为空" % path
    return "%s 目录内容：\n%s" % (path, "\n".join(entries))


def get_file_type(path):
    """获取指定文件的文件类型。"""
    if not os.path.exists(path):
        return "错误：文件不存在 %s" % path
    if os.path.isdir(path):
        return "%s 是目录" % path
    ext = os.path.splitext(path)[1].lower()
    desc = FILE_TYPES.get(ext, "未知类型文件")
    return "%s 的文件类型：%s" % (path, desc)


def get_file_content(path):
    """获取指定文件的内容，仅支持纯文本格式文件。"""
    if not os.path.isfile(path):
        return "错误：%s 不是有效文件" % path
    ext = os.path.splitext(path)[1].lower()
    if ext not in FILE_TYPES or ext in (".png", ".jpg", ".exe", ".pdf",
                                        ".docx", ".zip"):
        return "错误：%s 不是纯文本文件，无法读取内容" % path
    try:
        with open(path, "r", encoding="utf-8") as f:
            return "文件 %s 的内容：\n%s" % (path, f.read())
    except UnicodeDecodeError:
        return "错误：%s 不是 UTF-8 文本文件，无法读取" % path
    except Exception as e:
        return "读取失败：%s" % e


def create_file(directory, filename, content=""):
    """根据指定的目录和文件名创建新文件。"""
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        return "错误：文件已存在 %s，如需修改请使用编辑功能" % path
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "已创建文件：%s" % path
    except Exception as e:
        return "创建失败：%s" % e


def edit_file(path, content):
    """编辑指定文件的内容，仅支持纯文本格式文件。"""
    if not os.path.isfile(path):
        return "错误：%s 不是有效文件" % path
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "已更新文件：%s" % path
    except Exception as e:
        return "编辑失败：%s" % e


def create_directory(path):
    """创建新目录。"""
    try:
        os.makedirs(path, exist_ok=True)
        return "已创建目录：%s" % path
    except Exception as e:
        return "创建失败：%s" % e


def delete_directory(path):
    """删除目录，支持非空目录。"""
    if not os.path.isdir(path):
        return "错误：%s 不是有效目录" % path
    try:
        shutil.rmtree(path)
        return "已删除目录：%s" % path
    except Exception as e:
        return "删除失败：%s" % e


def delete_file(path):
    """删除文件。"""
    if not os.path.isfile(path):
        return "错误：%s 不是有效文件" % path
    try:
        os.remove(path)
        return "已删除文件：%s" % path
    except Exception as e:
        return "删除失败：%s" % e


def rename_file_or_dir(old_path, new_path):
    """重命名文件或目录。"""
    if not os.path.exists(old_path):
        return "错误：%s 不存在" % old_path
    if os.path.exists(new_path):
        return "错误：目标 %s 已存在" % new_path
    try:
        os.rename(old_path, new_path)
        return "已将 %s 重命名为 %s" % (old_path, new_path)
    except Exception as e:
        return "重命名失败：%s" % e


# ---------- function call 工具注册 ----------

def _params(properties, required):
    return {"type": "object", "properties": properties, "required": required}


TOOLS = [
    {"type": "function", "function": {"name": "getCWD",
        "description": "获取当前工作目录",
        "parameters": _params({}, [])}},
    {"type": "function", "function": {"name": "listDirectory",
        "description": "列出指定目录下所有文件和子目录",
        "parameters": _params({"path": {"type": "string",
            "description": "要列出的目录路径，默认当前目录"}}, [])}},
    {"type": "function", "function": {"name": "getFileType",
        "description": "获取指定文件的文件类型",
        "parameters": _params({"path": {"type": "string",
            "description": "文件路径"}}, ["path"])}},
    {"type": "function", "function": {"name": "getFileContent",
        "description": "获取指定文件的内容，仅支持纯文本格式文件",
        "parameters": _params({"path": {"type": "string",
            "description": "文件路径"}}, ["path"])}},
    {"type": "function", "function": {"name": "createFile",
        "description": "根据指定的目录和文件名创建新文件",
        "parameters": _params({
            "directory": {"type": "string", "description": "目标目录"},
            "filename": {"type": "string", "description": "文件名"},
            "content": {"type": "string", "description": "文件内容，可选"}},
            ["directory", "filename"])}},
    {"type": "function", "function": {"name": "editFile",
        "description": "编辑指定文件的内容，仅支持纯文本格式文件",
        "parameters": _params({
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "新的文件内容"}},
            ["path", "content"])}},
    {"type": "function", "function": {"name": "createDirectory",
        "description": "创建新目录",
        "parameters": _params({"path": {"type": "string",
            "description": "要创建的目录路径"}}, ["path"])}},
    {"type": "function", "function": {"name": "deleteDirectory",
        "description": "删除目录，支持非空目录",
        "parameters": _params({"path": {"type": "string",
            "description": "要删除的目录路径"}}, ["path"])}},
    {"type": "function", "function": {"name": "deleteFile",
        "description": "删除文件",
        "parameters": _params({"path": {"type": "string",
            "description": "要删除的文件路径"}}, ["path"])}},
    {"type": "function", "function": {"name": "renameFileOrDir",
        "description": "重命名文件或目录",
        "parameters": _params({
            "old_path": {"type": "string", "description": "原路径"},
            "new_path": {"type": "string", "description": "新路径"}},
            ["old_path", "new_path"])}},
]


def call_tool(name, args):
    """根据工具名分发到对应实现函数。"""
    if name == "getCWD":
        return get_cwd()
    if name == "listDirectory":
        return list_directory(args.get("path", "."))
    if name == "getFileType":
        return get_file_type(args["path"])
    if name == "getFileContent":
        return get_file_content(args["path"])
    if name == "createFile":
        return create_file(args["directory"], args["filename"],
                           args.get("content", ""))
    if name == "editFile":
        return edit_file(args["path"], args["content"])
    if name == "createDirectory":
        return create_directory(args["path"])
    if name == "deleteDirectory":
        return delete_directory(args["path"])
    if name == "deleteFile":
        return delete_file(args["path"])
    if name == "renameFileOrDir":
        return rename_file_or_dir(args["old_path"], args["new_path"])
    return "未知工具：%s" % name


def chat_with_tools(client, messages):
    """发送带 function call 的请求，自动执行工具并把结果回传给模型。"""
    response = client.chat.completions.create(
        model=client_kwargs["model"], messages=messages, tools=TOOLS)
    msg = response.choices[0].message

    if msg.tool_calls:
        assistant_msg = {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [{
                "id": tc.id, "type": "function",
                "function": {"name": tc.function.name,
                             "arguments": tc.function.arguments},
            } for tc in msg.tool_calls],
        }
        messages.append(assistant_msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = call_tool(tc.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": result})
        return chat_with_tools(client, messages)
    return msg.content


client_kwargs = {}


def main():
    try:
        cfg = load_config()
    except (FileNotFoundError, ValueError) as e:
        print("[配置错误] %s" % e)
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"],
                    timeout=DEFAULT_TIMEOUT)
    client_kwargs["model"] = cfg["model"]

    messages = [{"role": "system",
                 "content": "你是一个乐于助人的 AI 助手。涉及本地文件操作时，必须调用对应的文件操作工具，不要编造结果。"}]
    print("欢迎使用带本地文件操作工具的多轮对话，输入 exit 或 quit 退出。")

    try:
        while True:
            user_input = input("\nUser: ").strip()
            if not user_input:
                print("输入不能为空，请重新输入。")
                continue
            if user_input.lower() in EXIT_WORDS:
                print("再见，期待下次与你对话！")
                break

            messages.append({"role": "user", "content": user_input})
            trim_messages(messages)

            print("Assistant is thinking...", end="", flush=True)
            try:
                reply = chat_with_tools(client, messages)
            except Exception as e:
                print("\r[错误] %s" % e)
                messages.pop()
                continue

            messages.append({"role": "assistant", "content": reply})
            trim_messages(messages)
            print("\rAssistant: %s" % reply)
    except KeyboardInterrupt:
        print("\n再见，期待下次与你对话！")


if __name__ == "__main__":
    main()
