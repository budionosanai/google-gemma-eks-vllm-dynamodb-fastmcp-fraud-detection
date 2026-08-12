import os
import asyncio
from fastmcp import Client

ALB_URL = os.getenv("ALB_URL")
client = Client(f"http://{ALB_URL}/mcp")


async def main():
    async with client:
        print("=== FastMCP Client ===\n")

        print("Loading tools...")

        tools = await client.list_tools()
        tool_map = {tool.name: tool for tool in tools}

        print(f"Available tools: {list(tool_map.keys())}\n")

        if "check_transaction_fraud" not in tool_map:
            print("Tool check_transaction_fraud not found!")
            return

        print("Running fraud test #1...")
        result = await client.call_tool(
            "check_transaction_fraud",
            {
                "user_id": "Budiono Santoso",
                "amount": 120,
            },
        )
        print(result.content[0].text)

        print("\nRunning fraud test #2...")
        result = await client.call_tool(
            "check_transaction_fraud",
            {
                "user_id": "Budi Ajelah",
                "amount": 9500,
            },
        )
        print(result.content[0].text)

asyncio.run(main())