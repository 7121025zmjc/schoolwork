@echo off
cd /d "%~dp0"
python -m pet_hospital_mcp.server --transport stdio
