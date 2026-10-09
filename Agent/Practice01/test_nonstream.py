# -*- coding: utf-8 -*-
"""
test_nonstream.py —— 观察非流式输出效果的调试测试脚本

功能：
- 显式使用 stream=False 的非流式模式发送一条消息
- 打印请求发送与接收完成的时间戳
- 打印 token 使用情况 prompt_tokens、completion_tokens、total_tokens
- 打印完整响应对象，便于观察 API 返回的原始数据结构
- 复用 chat.py 中的配置读取与异常处理

运行：python test_nonstream.py
"""
import json
import sys
from datetime import datetime

from chat import load_config, describe_error


def now_str():
    """返回当前时间的可读字符串，精确到毫秒。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def main():
    # 1. 读取配置，出错时明确提示
    try:
        cfg = load_config()
    except Exception as e:
        hint, _ = describe_error(e)
        print("[配置错误] %s" % hint)
        sys.exit(1)

    from openai import OpenAI

    # 初始化客户端：非流式调试脚本同样走 OpenAI 兼容接口
    client = OpenAI(
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        timeout=30,
    )

    message = "你好，请做个自我介绍"
    messages = [{"role": "user", "content": message}]

    print("[用户] %s" % message)

    # 2. 记录请求发送时间戳
    t_send = now_str()
    print("[请求发送时间] %s" % t_send)

    # 3. 显式使用非流式模式发送请求
    try:
        response = client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            stream=False,
        )
    except Exception as e:
        hint, fatal = describe_error(e)
        print("[调用失败] %s" % hint)
        sys.exit(1 if fatal else 2)

    # 4. 记录接收完成时间戳
    t_recv = now_str()
    print("[接收完成时间] %s" % t_recv)

    # 5. 打印最终回复内容
    print("\n[模型回复]")
    print(response.choices[0].message.content)

    # 6. 打印响应元信息
    print("\n[响应元信息]")
    print("model: %s" % response.model)
    print("created 时间戳: %s" % response.created)
    print("finish_reason: %s" % response.choices[0].finish_reason)

    # 7. 打印 token 使用情况，API 未返回时给出说明
    print("\n[token 使用情况]")
    usage = response.usage
    if usage is not None:
        print("prompt_tokens: %s" % usage.prompt_tokens)
        print("completion_tokens: %s" % usage.completion_tokens)
        print("total_tokens: %s" % usage.total_tokens)
    else:
        print("API 未返回 usage 字段")

    # 8. 打印完整响应对象，便于观察原始数据结构
    print("\n[完整响应对象 JSON]")
    try:
        print(response.model_dump_json(indent=2))
    except AttributeError:
        print(json.dumps(response, default=str, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
