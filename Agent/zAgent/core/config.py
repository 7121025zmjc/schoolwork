# -*- coding: utf-8 -*-
"""配置加载模块：从 config.ini 读取 LLM 接口配置。"""
import configparser
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-3.5-turbo"


def load_config(path=CONFIG_FILE):
    """读取配置文件，返回 api_key、base_url、model 字典。"""
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

    return {
        "api_key": api_key,
        "base_url": config.get("LLM", "base_url",
                               fallback=DEFAULT_BASE_URL).strip(),
        "model": config.get("LLM", "model", fallback=DEFAULT_MODEL).strip(),
    }
