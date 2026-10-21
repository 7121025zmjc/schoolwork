# -*- coding: utf-8 -*-
"""工具模块：10 个本地文件操作工具 + getDate/isLeapYear 工具的注册表与实现，
业务层不依赖 UI。"""
import os
import shutil
import subprocess

FILE_TYPES = {
    ".txt": "纯文本文件", ".md": "Markdown 文本文件", ".py": "Python 源文件",
    ".json": "JSON 数据文件", ".ini": "配置文件", ".csv": "CSV 表格文件",
    ".html": "HTML 网页文件", ".css": "CSS 样式文件", ".js": "JavaScript 源文件",
    ".png": "PNG 图片", ".jpg": "JPEG 图片", ".exe": "可执行程序",
    ".pdf": "PDF 文档", ".docx": "Word 文档", ".zip": "压缩包",
}

BINARY_EXTS = (".png", ".jpg", ".exe", ".pdf", ".docx", ".zip")


def get_date():
    """调用本地 date 命令获取当前日期和时间。"""
    try:
        date_str = subprocess.run(
            ["cmd", "/c", "date", "/t"], capture_output=True, text=True,
            timeout=10).stdout.strip()
        time_str = subprocess.run(
            ["cmd", "/c", "time", "/t"], capture_output=True, text=True,
            timeout=10).stdout.strip()
        return "当前日期：%s，当前时间：%s" % (date_str, time_str)
    except Exception as e:
        return "获取日期失败：%s" % e


def is_leap_year(year):
    """用 Python 代码判断指定年份是否为闰年。"""
    year = int(year)
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


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
    if ext not in FILE_TYPES or ext in BINARY_EXTS:
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
    {"type": "function", "function": {"name": "getDate",
        "description": "获取当前电脑的日期和时间",
        "parameters": _params({}, [])}},
    {"type": "function", "function": {"name": "isLeapYear",
        "description": "判断指定年份是否为闰年",
        "parameters": _params({"year": {"type": "integer",
            "description": "要判断的年份"}}, ["year"])}},
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
    if name == "getDate":
        return get_date()
    if name == "isLeapYear":
        is_leap = is_leap_year(args.get("year"))
        return "%s 年是闰年" % args["year"] if is_leap else "%s 年不是闰年" % args["year"]
    return "未知工具：%s" % name
