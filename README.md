# Schoolwork

AI+应用系统开发实训课程作业仓库。

## 目录结构

| 目录 | 说明 |
| --- | --- |
| PetHospitalMCP | 宠物医院服务 MCP，封装统计宠物数量、查询宠物档案等工具 |
| AnythingLLMMCP | AnythingLLM MCP Server，Streamable HTTP 方式，提取第一个工作区的文件信息 |
| AnythingLLMWebPage | 文档上传网页，上传文件到第一个工作区并完成向量化嵌入 |
| Agent/Practice01 | 多轮对话程序，支持非流式、流式输出和聊天历史上下文 |

## 使用说明

各项目均使用 `config.ini` 存放配置，该文件已被 .gitignore 排除，需自行创建。

| 项目 | 配置 |
| --- | --- |
| PetHospitalMCP | 宠物医院服务地址 http://127.0.0.1:8080 |
| AnythingLLMMCP | AnythingLLM 地址和 API key，默认 http://localhost:3001 |
| AnythingLLMWebPage | 同上 |
| Agent/Practice01 | LLM 服务地址、模型和 api_key，如本地 LM Studio http://127.0.0.1:1234/v1 |
