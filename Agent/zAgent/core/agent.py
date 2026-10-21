# -*- coding: utf-8 -*-
"""Agent 核心模块：封装 LLM 客户端与 function call 循环，供各 UI 层复用。"""
import json

from openai import OpenAI

from core.tools import TOOLS, call_tool

DEFAULT_TIMEOUT = 60
MAX_MESSAGES = 30
SYSTEM_PROMPT = ("你是一个乐于助人的 AI 助手。涉及本地文件操作时，"
                 "必须调用对应的文件操作工具，不要编造结果。")


class Agent:
    """LLM 智能体：管理会话上下文并执行 function call 循环。

    UI 层只需创建 Agent 并调用 chat 方法，不感知工具细节。
    """

    def __init__(self, cfg, system_prompt=SYSTEM_PROMPT):
        self.client = OpenAI(api_key=cfg["api_key"],
                             base_url=cfg["base_url"],
                             timeout=DEFAULT_TIMEOUT)
        self.model = cfg["model"]
        self.messages = [{"role": "system", "content": system_prompt}]

    def trim_messages(self):
        """消息条数超过上限时，截断最早的对话，保留系统提示。"""
        if len(self.messages) <= MAX_MESSAGES:
            return
        excess = len(self.messages) - MAX_MESSAGES
        del self.messages[1:1 + excess]

    def chat(self, user_input):
        """发送用户消息，自动执行工具调用，返回最终文本回复。"""
        self.messages.append({"role": "user", "content": user_input})
        self.trim_messages()
        reply = self._chat_with_tools()
        self.messages.append({"role": "assistant", "content": reply})
        self.trim_messages()
        return reply

    def _chat_with_tools(self):
        """function call 循环：请求模型，必要时执行工具并递归回传结果。"""
        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages, tools=TOOLS)
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
            self.messages.append(assistant_msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                result = call_tool(tc.function.name, args)
                self.messages.append({"role": "tool",
                                      "tool_call_id": tc.id,
                                      "content": result})
            return self._chat_with_tools()
        return msg.content
