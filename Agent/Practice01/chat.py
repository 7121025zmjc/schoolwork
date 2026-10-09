# -*- coding: utf-8 -*-
"""
chat.py —— 与大语言模型 LLM 的多轮对话脚本

功能：
- 从同目录的 config.ini 读取接口配置 api_key、base_url、model
- 持续多轮对话，携带完整历史上下文，模型能记住之前聊过的内容
- 输入 exit 或 quit 退出，Ctrl+C 也能安全退出
- 消息条数超过上限时自动截断最早的对话，防止超出上下文窗口
- 优先使用 openai 库，未安装时自动降级为 requests 直接调用兼容接口

依赖安装：pip install openai requests
"""
import configparser
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")     # 配置文件固定在脚本目录下
DEFAULT_TIMEOUT = 30                    # API 请求超时时间，单位秒
DEFAULT_BASE_URL = "https://api.openai.com/v1"   # base_url 缺失时的默认值
DEFAULT_MODEL = "gpt-3.5-turbo"         # model 缺失时的默认值
MAX_MESSAGES = 20                       # 消息列表条数上限，防止超出上下文窗口
EXIT_WORDS = ("exit", "quit")           # 用户输入这些词时退出


def load_config(path=CONFIG_FILE):
    """读取配置文件，返回包含 api_key、base_url、model 的字典。

    文件不存在、缺少 [LLM] 段、api_key 为空时抛出带说明的异常；
    base_url、model 缺失时使用默认值，保证脚本仍可运行。
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            "未找到配置文件 %s，请先参照以下格式创建：\n"
            "[LLM]\n"
            "api_key = your_api_key_here\n"
            "base_url = https://api.openai.com/v1\n"
            "model = gpt-3.5-turbo" % path
        )

    config = configparser.ConfigParser()

    # 读取配置文件，格式错误时转为友好提示
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
    """消息条数超过上限时，截断最早的对话，保留系统提示和最近内容。

    messages[0] 固定为系统提示，从索引 1 开始删除最早的消息。
    """
    if len(messages) <= MAX_MESSAGES:
        return
    excess = len(messages) - MAX_MESSAGES
    del messages[1:1 + excess]


def chat_with_openai(cfg, messages):
    """首选方案：使用 openai 官方库发送带上下文的对话请求，返回回复文本。"""
    from openai import OpenAI

    # 初始化客户端：传入 API Key、自定义 base_url 和超时时间
    client = OpenAI(
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        timeout=DEFAULT_TIMEOUT,
    )

    # 发送对话请求，messages 携带全部历史记录
    response = client.chat.completions.create(
        model=cfg["model"],
        messages=messages,
    )

    if not response.choices:
        raise RuntimeError("模型未返回任何内容，choices 为空。")

    return response.choices[0].message.content


def chat_with_requests(cfg, messages):
    """备选方案：openai 库不可用时，用 requests 直接调用兼容接口。"""
    import requests

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": "Bearer %s" % cfg["api_key"],
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg["model"],
        "messages": messages,
    }

    # 发送 POST 请求，非 2xx 状态码会被 raise_for_status 转为异常
    resp = requests.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()

    data = resp.json()
    if not data.get("choices"):
        raise RuntimeError("模型未返回任何内容，choices 为空。")

    return data["choices"][0]["message"]["content"]


def chat_once(cfg, messages):
    """执行一次对话：优先 openai 库，导入失败时降级为 requests。"""
    try:
        return chat_with_openai(cfg, messages)
    except ImportError:
        try:
            return chat_with_requests(cfg, messages)
        except ImportError:
            raise RuntimeError("缺少依赖库，请先执行：pip install openai requests")


def describe_error(e):
    """将异常映射为友好的中文提示，返回提示文本和是否致命两个值。"""
    if isinstance(e, (FileNotFoundError, ValueError)):
        return str(e), True

    # 匹配 openai 库的异常类型，仅在该库可用时生效
    try:
        import openai
    except ImportError:
        openai = None

    if openai is not None:
        if isinstance(e, openai.AuthenticationError):
            return "认证失败：API Key 无效或已过期，请检查 config.ini 中的 api_key。", True
        if isinstance(e, openai.RateLimitError):
            return "请求过于频繁，已触发限流，请稍后重试。", False
        if isinstance(e, openai.APITimeoutError):
            return "请求超时：模型响应时间过长，请稍后重试或增大超时时间。", False
        if isinstance(e, openai.APIConnectionError):
            return "网络连接失败：请检查网络，或确认 base_url 配置正确。", False
        if isinstance(e, openai.APIStatusError):
            msg = getattr(e, "message", str(e))
            return "接口返回错误码 %s：%s" % (e.status_code, msg), False

    # 匹配 requests 备选路径的异常类型
    try:
        import requests
    except ImportError:
        requests = None

    if requests is not None:
        if isinstance(e, requests.exceptions.Timeout):
            return "请求超时：请检查网络或稍后重试。", False
        if isinstance(e, requests.exceptions.ConnectionError):
            return "网络连接失败：请检查网络或 base_url 配置。", False
        if isinstance(e, requests.exceptions.HTTPError):
            status = e.response.status_code if e.response is not None else "未知"
            if status == 401:
                return "认证失败，HTTP 401：API Key 无效或已过期。", True
            if status == 404:
                return "接口地址不存在，HTTP 404：请检查 base_url。", True
            return "接口返回错误码 %s：请检查请求参数或稍后重试。" % status, False

    return "请求失败：%s" % e, False


def main():
    """主流程：读取配置后进入多轮对话循环。"""
    # 1. 读取配置，文件不存在、字段缺失等在此统一处理
    try:
        cfg = load_config()
    except (FileNotFoundError, ValueError) as e:
        print("[配置错误] %s" % e)
        sys.exit(1)

    # 2. 初始化上下文：第一条为系统提示，之后的对话按顺序追加
    messages = [{"role": "system", "content": "你是一个乐于助人的 AI 助手。"}]

    print("欢迎使用多轮对话，输入 exit 或 quit 退出，Ctrl+C 也可以随时结束。")

    try:
        while True:
            # 3. 读取用户输入，空输入时提示重新输入
            user_input = input("\nUser: ").strip()
            if not user_input:
                print("输入不能为空，请重新输入。")
                continue

            # 4. 检测退出指令，打印告别语后结束循环
            if user_input.lower() in EXIT_WORDS:
                print("再见，期待下次与你对话！")
                break

            # 5. 将本次用户消息加入上下文并发送
            messages.append({"role": "user", "content": user_input})
            trim_messages(messages)

            # 6. 等待模型回复时给出提示
            print("Assistant is thinking...", end="", flush=True)
            try:
                reply = chat_once(cfg, messages)
            except Exception as e:
                # 单次调用失败不退出，回退掉出错的用户消息后继续对话
                hint, fatal = describe_error(e)
                print("\r[错误] %s" % hint)
                messages.pop()
                continue

            # 7. 将模型回复加入上下文，覆盖 thinking 提示后打印
            messages.append({"role": "assistant", "content": reply})
            trim_messages(messages)
            print("\rAssistant: %s" % reply)

    except KeyboardInterrupt:
        # 8. 捕获 Ctrl+C，安全退出
        print("\n再见，期待下次与你对话！")


if __name__ == "__main__":
    main()
