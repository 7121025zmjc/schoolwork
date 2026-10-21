# -*- coding: utf-8 -*-
"""tui 前端：Textual 终端聊天界面，仅依赖 core 的接口。
未来新增 web、desktop、mobile 前端时，与 tui 平级创建目录即可。"""
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, RichLog

from core.agent import Agent

EXIT_WORDS = ("exit", "quit")


class ChatTUI(App):
    """终端聊天界面，通过 Agent 与 LLM 对话。"""

    TITLE = "zAgent TUI"

    def __init__(self, agent):
        super().__init__()
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(highlight=True, markup=True)
        yield Input(placeholder="输入消息，exit 或 quit 退出")
        yield Footer()

    def on_mount(self):
        self.query_one(RichLog).write(
            "[bold green]欢迎使用 zAgent，输入消息开始对话[/]")

    def on_input_submitted(self, event):
        text = event.value.strip()
        if not text:
            return
        event.input.value = ""
        log = self.query_one(RichLog)
        log.write("[bold cyan]User:[/] %s" % text)
        if text.lower() in EXIT_WORDS:
            self.exit()
            return
        try:
            reply = self.agent.chat(text)
            log.write("[bold green]Assistant:[/] %s" % reply)
        except Exception as e:
            log.write("[bold red]错误:[/] %s" % e)
