# -*- coding: utf-8 -*-
"""tui 前端：Textual 终端聊天界面，仅依赖 core 的接口。
未来新增 web、desktop、mobile 前端时，与 tui 平级创建目录即可。"""
import threading
import time

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, RichLog, Static

from core.agent import Agent

EXIT_WORDS = ("exit", "quit")


class ChatTUI(App):
    """终端聊天界面，实时展示 AI 思考、工具调用和流式回答。"""

    TITLE = "zAgent"
    SUB_TITLE = "core + TUI"

    CSS = """
    Screen {
        background: #0d1117;
    }
    Header {
        background: #161b22;
        color: #e6edf3;
    }
    #chat {
        border: round #30363d;
        background: #0d1117;
        height: 1fr;
    }
    #output {
        height: 3;
        border: round #1f6feb;
        background: #10151c;
        color: #58a6ff;
        padding: 0 1;
        display: none;
        dock: bottom;
    }
    Input {
        border: round #30363d;
        background: #161b22;
        color: #e6edf3;
    }
    Input:focus {
        border: round #3fb950;
    }
    """

    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self._last_stream_render = 0.0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="chat", highlight=True, wrap=True)
        yield Static("", id="output")
        yield Input(placeholder="输入消息，exit 或 quit 退出")
        yield Footer()

    def on_mount(self):
        model = self.agent.model
        self.query_one(RichLog).write(
            Text("欢迎使用 zAgent，当前模型 %s，输入消息开始对话" % model,
                 style="bold #3fb950"))

    def on_input_submitted(self, event):
        text = event.value.strip()
        if not text:
            return
        event.input.value = ""
        if text.lower() in EXIT_WORDS:
            self.exit()
            return
        self.query_one(RichLog).write(
            Text("你  %s" % text, style="bold #58a6ff"))
        threading.Thread(target=self._run_chat, args=(text,),
                         daemon=True).start()

    def _run_chat(self, text):
        """后台线程执行对话，事件通过 call_from_thread 回主线程更新 UI。"""
        def emit(event_name, data):
            self.call_from_thread(self._on_event, event_name, data)

        self.agent.on_event = emit
        try:
            reply = self.agent.chat(text)
            self.call_from_thread(self._finish, reply)
        except Exception as e:
            self.call_from_thread(self._finish,
                                  "错误：%s" % e)

    def _on_event(self, event_name, data):
        if event_name == "thinking":
            self._set_output("● AI 思考中...")
        elif event_name == "tool":
            name = data.get("name", "")
            args = data.get("args") or {}
            result = str(data.get("result", ""))
            arg_str = "，".join("%s=%s" % (k, v) for k, v in args.items())
            self.query_one(RichLog).write(
                Text("工具 %s 参数 %s\n结果 %s" % (name, arg_str, result),
                     style="bold #d29922"))
            self._set_output("● AI 正在使用工具 %s..." % name)
        elif event_name == "stream":
            now = time.time()
            if now - self._last_stream_render >= 0.06:
                self._last_stream_render = now
                self._set_output("● AI 生成中... %s" % data.get("text", ""))

    def _set_output(self, text):
        output = self.query_one("#output", Static)
        output.display = True
        output.update(text)

    def _finish(self, reply):
        output = self.query_one("#output", Static)
        output.display = False
        output.update("")
        self.query_one(RichLog).write(
            Text("AI  %s" % reply, style="bold #3fb950"))
