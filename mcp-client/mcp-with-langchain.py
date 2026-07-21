import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

ALB_URL = "http://ALB_DNS_name/mcp"


async def main():
    print("=== LangChain MCP Client ===\n")

    client = MultiServerMCPClient(
        {
            "fraud": {
                "transport": "http",
                "url": ALB_URL,
            }
        }
    )

    print("Loading tools...")

    tools = await client.get_tools()
    tool_map = {tool.name: tool for tool in tools}

    print(f"Available tools: {[tool.name for tool in tools]}\n")

    if "check_transaction_fraud" not in tool_map:
        print("Tool check_transaction_fraud not found!")
        return

    print("Running fraud test #1...")
    result = await tool_map["check_transaction_fraud"].ainvoke(
        {
            "user_id": "Budiono Santoso",
            "amount": 120,
        }
    )
    print(result[0]["text"])

    print("Running fraud test #2...")
    result = await tool_map["check_transaction_fraud"].ainvoke(
        {
            "user_id": "Budi Ajelah",
            "amount": 9500,
        }
    )
    print(result[0]["text"])


asyncio.run(main())