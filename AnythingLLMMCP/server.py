# -*- coding: utf-8 -*-
"""
AnythingLLM MCP Server
Streamable HTTP 方式，同时兼容 MCP 新旧协议：不强制 initialize 握手、不要求长连接。
只用标准库运行，无第三方依赖。启动后 MCP 端点为 http://localhost:8000/mcp
"""
import configparser
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8000


def load_config():
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(BASE_DIR, "config.ini"), encoding="utf-8")
    sec = cfg["ANYTHINGLLM"] if "ANYTHINGLLM" in cfg else {}
    return sec.get("api_key", ""), sec.get("base_url", "http://localhost:3001").rstrip("/")


API_KEY, BASE_URL = load_config()


def api(path, method="GET", payload=None):
    headers = {"Authorization": "Bearer " + API_KEY}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE_URL + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def get_first_workspace_files():
    """第一个工作区提取文件信息"""
    data = api("/api/v1/workspaces")
    workspaces = data.get("workspaces", [])
    if not workspaces:
        return "AnythingLLM 中没有任何工作区"
    first = workspaces[0]
    slug = first["slug"]
    detail = api("/api/v1/workspace/" + slug)
    ws = detail.get("workspace", detail)
    docs = ws.get("documents", [])
    lines = ["工作区：%s（%s）" % (first.get("name", slug), slug)]
    if not docs:
        lines.append("该工作区暂无文件")
    for d in docs:
        lines.append("- 文件：%s，已解析：%s，位置：%s" % (
            d.get("title", "?"), d.get("parsed", False), d.get("location", "?")))
    return "\n".join(lines)


TOOLS = [{
    "name": "get_first_workspace_files",
    "description": "获取 AnythingLLM 第一个工作区里的文件信息，返回文件名、解析状态和存储位置",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
}]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        self._send(200, {"jsonrpc": "2.0",
                         "result": {"name": "anythingllm-mcp", "version": "1.0.0",
                                    "endpoint": "/mcp"}})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            req = json.loads(raw)
        except ValueError:
            req = {}
        method, rid = req.get("method", ""), req.get("id")

        if method == "initialize":
            self._send(200, {"jsonrpc": "2.0", "id": rid,
                             "result": {"protocolVersion": "2025-03-26",
                                        "capabilities": {"tools": {}},
                                        "serverInfo": {"name": "anythingllm-mcp",
                                                       "version": "1.0.0"}}})
        elif method.startswith("notifications/"):
            self.send_response(202)
            self.end_headers()
        elif method == "tools/list":
            self._send(200, {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            try:
                text = get_first_workspace_files()
                self._send(200, {"jsonrpc": "2.0", "id": rid,
                                 "result": {"content": [{"type": "text", "text": text}]}})
            except Exception as e:
                self._send(200, {"jsonrpc": "2.0", "id": rid,
                                 "result": {"content": [{"type": "text", "text": "调用失败：" + str(e)}],
                                            "isError": True}})
        else:
            self._send(200, {"jsonrpc": "2.0", "id": rid, "result": {}})


if __name__ == "__main__":
    if not API_KEY or API_KEY == "your_api_key_here":
        raise SystemExit("请先在 config.ini 填入 AnythingLLM 的 api_key")
    print("AnythingLLM MCP 已启动：http://localhost:%d/mcp" % PORT)
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
