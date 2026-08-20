import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_tool(session, name, arguments):
    result = await session.call_tool(name, arguments)

    print(f"\n=== {name} ===")

    for content in result.content:
        if hasattr(content, "text"):
            try:
                parsed = json.loads(content.text)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print(content.text)
        else:
            print(content)


async def main():

    server_params = StdioServerParameters(
        command="python",
        args=["-m", "app.sor.server"],
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\n=== MCP TOOLS ===")

            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"- {tool.name}")

            await call_tool(
                session,
                "list_accounts",
                {},
            )

            await call_tool(
                session,
                "get_account",
                {
                    "account_id": "northline-grid",
                },
            )

            await call_tool(
                session,
                "list_account_documents",
                {
                    "account_id": "northline-grid",
                },
            )

            await call_tool(
                session,
                "get_account_document",
                {
                    "account_id": "northline-grid",
                    "filename": "02_security_review.md",
                },
            )

            await call_tool(
                session,
                "get_account_usage",
                {
                    "account_id": "northline-grid",
                },
            )

            await call_tool(
                session,
                "search_documents",
                {
                    "query": "hardware",
                },
            )


if __name__ == "__main__":
    asyncio.run(main())