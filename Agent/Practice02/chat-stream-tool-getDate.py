# -*- coding: utf-8 -*-
"""
chat-stream-tool-getDate.py —— 多轮对话 + function call 工具 getDate
基于 Practice01 的 chat.py 开发，新增 function call tool getDate：
- 获取当前电脑的日期和时间
- 按要求使用调用本地 date 命令的方式，不编写 Python 代码取时间
运行：python chat-stream-tool-getDate.py
"""
import configparser
import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")
DEFAULT_TIMEOUT = 30
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_MESSAGES = 20
EXIT_WORDS = ("exit", "quit")


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


TOOLS = [{
    "type": "function",
    "function": {
        "name": "getDate",
        "description": "获取当前电脑的日期和时间",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}]


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
            if tc.function.name == "getDate":
                result = get_date()
            else:
                result = "未知工具：%s" % tc.function.name
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
                 "content": "你是一个乐于助人的 AI 助手。获取日期时间时使用 getDate 工具。"}]
    print("欢迎使用带 getDate 工具的多轮对话，输入 exit 或 quit 退出。")

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
