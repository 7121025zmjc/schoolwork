# -*- coding: utf-8 -*-
"""
chat_stream.py —— 流式输出 Stream 模式的打字机效果脚本

功能：
- 使用 openai 库的流式请求方式 stream=True
- 逐块接收模型回复并立即打印到控制台，模拟打字机效果
- 复用 chat.py 中的配置读取与异常处理

运行：python chat_stream.py
"""
import sys
import time

from chat import load_config, describe_error


def main():
    # 1. 读取配置，出错时明确提示
    try:
        cfg = load_config()
    except Exception as e:
        hint, _ = describe_error(e)
        print("[配置错误] %s" % hint)
        sys.exit(1)

    from openai import OpenAI

    # 初始化客户端：timeout 同时作用于流式接收，超时会抛 APITimeoutError
    client = OpenAI(
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        timeout=30,
    )

    message = "你好，请做个自我介绍"
    messages = [{"role": "user", "content": message}]

    print("[用户] %s\n" % message)
    print("[%s] 回复：" % cfg["model"], end="", flush=True)

    try:
        # 2. 发起流式请求：stream=True 让 API 把回复切成多个 chunk 逐块返回
        stream = client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            stream=True,
        )

        # 3. 逐块接收并立即打印，形成打字机效果
        for chunk in stream:
            # 每个 chunk 的增量文本位于 choices[0].delta.content
            # 首尾 chunk 可能没有 choices 或 content 为空，需要逐层判空
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
                time.sleep(0.01)  # 极短延迟，让文字逐个出现更自然

        print()  # 4. 流式结束后补换行，让输出保持完整

    except KeyboardInterrupt:
        # 用户按 Ctrl+C 手动中断流式输出
        print("\n[已中断] 你手动停止了输出。")
        sys.exit(130)
    except Exception as e:
        # 连接中断、接收超时、接口错误等统一在此处理
        print()
        hint, fatal = describe_error(e)
        print("[流式传输错误] %s" % hint)
        sys.exit(1 if fatal else 2)


if __name__ == "__main__":
    main()
