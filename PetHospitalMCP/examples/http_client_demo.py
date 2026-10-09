import asyncio

from mcp import Client


async def main() -> None:
    async with Client("http://127.0.0.1:8000/mcp") as client:
        result = await client.call_tool("health_check", {})
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
