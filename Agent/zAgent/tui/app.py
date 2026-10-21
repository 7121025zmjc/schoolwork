# -*- coding: utf-8 -*-
"""tui 前端：Textual 终端聊天界面，气泡消息流 + 工具活动面板。
未来新增 web、desktop、mobile 前端时，与 tui 平级创建目录即可。"""
import threading

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, LoadingIndicator, Static

from core.agent import Agent

EXIT_WORDS = ("exit", "quit")

BUBBLE_CSS = {
    "you": ("#1f6feb", "#e8f1ff", "#d5e6ff"),
    "ai": ("#1a7f37", "#e9f6ec", "#d3f0da"),
    "tool": ("#9a6700", "#fff8e5", "#f5e6b8"),
    "err": ("#d1242f", "#fdebec", "#f6cdd0"),
}


class Bubble(Static):
    """消息气泡，按角色着色。"""


class ChatTUI(App):
    """zAgent 终端聊天界面：左侧对话流，右侧工具活动，底部状态条。"""

    TITLE = "zAgent"

    CSS = """
    Screen {
        background: #f6f8fa;
    }
    Header {
        background: #ffffff;
        color: #24292f;
        border-bottom: solid #d0d7de;
    }
    #chat_col {
        width: 3fr;
        border-right: solid #d0d7de;
        background: #f6f8fa;
    }
    #tools_col {
        width: 2fr;
        background: #ffffff;
    }
    #messages {
        height: 1fr;
        padding: 1 1;
        background: #f6f8fa;
    }
    Bubble {
        width: 100%;
        padding: 0 1;
        margin-bottom: 1;
    }
    #tools_title {
        background: #f6f8fa;
        color: #57606a;
        padding: 0 1;
        text-style: bold;
        border-bottom: solid #d0d7de;
    }
    #tool_list {
        height: 1fr;
        padding: 0 1;
        background: #ffffff;
    }
    #status {
        height: 3;
        background: #ffffff;
        border-top: solid #d0d7de;
        padding: 0 1;
        color: #57606a;
    }
    #status_text {
        width: 1fr;
    }
    #status_loading {
        width: auto;
    }
    Input {
        border: solid #d0d7de;
        background: #ffffff;
        color: #24292f;
    }
    Input:focus {
        border: solid #0969da;
    }
    """

    def __init__(self, agent):
        super().__init__()
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="chat_col"):
                yield VerticalScroll(id="messages")
                yield Input(placeholder="输入消息，exit 或 quit 退出")
            with Vertical(id="tools_col"):
                yield Static("工具活动", id="tools_title")
                yield VerticalScroll(id="tool_list")
        with Horizontal(id="status"):
            yield LoadingIndicator(id="status_loading")
            yield Static("就绪，输入消息开始对话", id="status_text")
        yield Footer()

    def on_mount(self):
        model = self.agent.model
        self.run_worker(self._add_bubble(
            "欢迎使用 zAgent，当前模型 %s\n可以问日期、闰年、文件操作" % model,
            "ai"))

    def on_input_submitted(self, event):
        text = event.value.strip()
        if not text:
            return
        event.input.value = ""
        if text.lower() in EXIT_WORDS:
            self.exit()
            return
        self.run_worker(self._add_bubble("你  " + text, "you"))
        threading.Thread(target=self._run_chat, args=(text,),
                         daemon=True).start()

    def _run_chat(self, text):
        """后台线程执行对话，事件通过 call_from_thread 回主线程更新 UI。"""
        def emit(event_name, data):
            self.call_from_thread(self._on_event, event_name, data)

        self.agent.on_event = emit
        try:
            reply = self.agent.chat(text)
            self.call_from_thread(self._on_event, "final", {"text": reply})
        except Exception as e:
            self.call_from_thread(self._on_event, "error", {"text": str(e)})

    def _on_event(self, event_name, data):
        if event_name == "thinking":
            self._set_status("AI 思考中...", loading=True)
        elif event_name == "tool":
            name = data.get("name", "")
            args = data.get("args") or {}
            result = str(data.get("result", ""))
            arg_str = "，".join("%s=%s" % (k, v) for k, v in args.items())
            line = "%s\n  参数 %s\n  结果 %s" % (name, arg_str, result)
            self.run_worker(self._add_bubble("工具  " + name + "  " + arg_str,
                                             "tool"))
            self.run_worker(self._add_tool_line(
                "%s\n参数 %s\n结果 %s" % (name, arg_str, result)))
            self._set_status("正在执行工具 %s..." % name, loading=True)
        elif event_name == "stream":
            self._set_status("AI 生成中..." + data.get("text", ""),
                             loading=True)
        elif event_name == "final":
            self.run_worker(self._add_bubble("AI  " + data.get("text", ""),
                                             "ai"))
            self._set_status("就绪，输入消息开始对话", loading=False)
        elif event_name == "error":
            self.run_worker(self._add_bubble("错误  " + data.get("text", ""),
                                             "err"))
            self._set_status("就绪，输入消息开始对话", loading=False)

    def _set_status(self, text, loading):
        self.query_one("#status_text", Static).update(text)
        self.query_one("#status_loading",
                       LoadingIndicator).display = loading

    async def _add_bubble(self, text, role):
        color, bg, border = BUBBLE_CSS.get(role, BUBBLE_CSS["ai"])
        bubble = Bubble(text)
        bubble.styles.border = ("solid", border)
        bubble.styles.color = color
        bubble.styles.background = bg
        await self.query_one("#messages", VerticalScroll).mount(bubble)
        self.query_one("#messages", VerticalScroll).scroll_end(
            animate=True)

    async def _add_tool_line(self, text):
        line = Static(text)
        line.styles.color = "#9a6700"
        line.styles.background = "#fff8e5"
        line.styles.border = ("solid", "#f5e6b8")
        await self.query_one("#tool_list", VerticalScroll).mount(line)
        self.query_one("#tool_list", VerticalScroll).scroll_end(
            animate=True)
