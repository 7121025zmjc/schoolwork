# -*- coding: utf-8 -*-
"""
AnythingLLM 文档上传网页
把文件上传到第一个工作区并完成向量化嵌入。
依赖：pip install flask requests
启动：python app.py  然后浏览器打开 http://localhost:5000
"""
import configparser
import os

import requests
from flask import Flask, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 5000

cfg = configparser.ConfigParser()
cfg.read(os.path.join(BASE_DIR, "config.ini"), encoding="utf-8")
API_KEY = cfg["ANYTHINGLLM"].get("api_key", "")
BASE_URL = cfg["ANYTHINGLLM"].get("base_url", "http://localhost:3001").rstrip("/")

app = Flask(__name__)
HEADERS = {"Authorization": "Bearer " + API_KEY}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>上传文档到 AnythingLLM</title></head>
<body style="font-family:sans-serif;max-width:560px;margin:40px auto">
<h2>上传文档到第一个工作区</h2>
<form method=post enctype=multipart/form-data action=/upload>
<input type=file name=file required>
<button type=submit>上传并嵌入</button>
</form><p style=color:#888>$MSG</p></body></html>"""


def first_workspace_slug():
    r = requests.get(BASE_URL + "/api/v1/workspaces", headers=HEADERS, timeout=30)
    r.raise_for_status()
    ws = r.json().get("workspaces", [])
    if not ws:
        raise RuntimeError("没有工作区，请先在 AnythingLLM 创建")
    return ws[0]["slug"]


@app.route("/")
def index():
    return PAGE.replace("$MSG", "")


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    slug = first_workspace_slug()
    r = requests.post(BASE_URL + "/api/v1/document/upload",
                      headers=HEADERS,
                      files={"file": (f.filename, f.stream.read())},
                      timeout=120)
    r.raise_for_status()
    location = r.json()["documents"][0]["location"]
    requests.post(BASE_URL + "/api/v1/workspace/%s/update-embeddings" % slug,
                  headers={**HEADERS, "Content-Type": "application/json"},
                  json={"adds": [location], "deletes": []}, timeout=120).raise_for_status()
    return PAGE.replace("$MSG", "已上传并完成嵌入：%s" % f.filename)


if __name__ == "__main__":
    if API_KEY == "your_api_key_here" or not API_KEY:
        raise SystemExit("请先在 config.ini 填入 AnythingLLM 的 api_key")
    app.run(port=PORT, debug=False)
