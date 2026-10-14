@echo off
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" -m pet_hospital_mcp.server --transport streamable-http --host 127.0.0.1 --port 8090
