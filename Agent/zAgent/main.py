# -*- coding: utf-8 -*-
"""zAgent 入口：core 业务与 ui 界面解耦，切换界面只需替换 run 的调用。"""
import sys

from core.agent import Agent
from core.config import load_config


def run():
    try:
        cfg = load_config()
    except (FileNotFoundError, ValueError) as e:
        print("[配置错误] %s" % e)
        sys.exit(1)

    agent = Agent(cfg)

    # 前端入口：需要开发 web / desktop / mobile 版本时，替换此处即可
    from tui.app import ChatTUI
    ChatTUI(agent).run()


if __name__ == "__main__":
    run()
