# Pet Hospital MCP 运行说明

## 1. 启动 Go 服务

在仓库根目录启动：

```bat
cd /d D:\2x\windows
pethospital.exe -addr 127.0.0.1:8080
```

如果你仍在源码模式：

```bat
go run . -addr 127.0.0.1:8080
```

## 2. 启动 MCP 服务（HTTP 模式，适合调试）

```bat
cd /d D:\2x\windows\pet-hospital-mcp
python -m pet_hospital_mcp.server --transport streamable-http --host 127.0.0.1 --port 8000
```

MCP 地址：

```text
http://127.0.0.1:8000/mcp
```

## 3. 先验证底层 Go API

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/v1/stats
curl "http://127.0.0.1:8080/api/v1/pets?page=1&pageSize=3"
```

## 4. 运行 smoke test

```bat
cd /d D:\2x\windows\pet-hospital-mcp
python scripts\smoke_test.py
```

## 5. MCP 配置（stdio 模式）

```json
{
  "servers": {
    "pet-hospital": {
      "command": "python",
      "args": [
        "-m",
        "pet_hospital_mcp.server",
        "--transport",
        "stdio"
      ],
      "env": {
        "PET_HOSPITAL_API_BASE_URL": "http://127.0.0.1:8080",
        "MCP_TRANSPORT": "stdio"
      },
      "cwd": "D:/2x/windows/pet-hospital-mcp"
    }
  }
}
```

## 6. 关键验证点

- `GET /health` 返回 200
- `GET /api/v1/pets` 返回宠物列表
- MCP HTTP 地址在 `127.0.0.1:8000/mcp` 可访问
- `list_pets` 工具可被 MCP client 调用
