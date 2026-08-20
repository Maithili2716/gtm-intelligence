import os

import httpx
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


load_dotenv()


class FlytBaseSOR:

    """
    MCP client for the GTM Intelligence Source of Truth.

    The rest of the intelligence system only knows this interface.
    It does not know how the underlying Book of Business is stored.
    """

    def __init__(self):

        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "app.sor.server"],
        )

    async def _call(
        self,
        tool_name: str,
        arguments: dict | None = None,
    ):

        async with stdio_client(
            self.server_params
        ) as (read, write):

            async with ClientSession(
                read,
                write,
            ) as session:

                await session.initialize()

                return await session.call_tool(
                    tool_name,
                    arguments or {},
                )

    async def list_accounts(self):
        return await self._call(
            "list_accounts"
        )

    async def get_account(
        self,
        account_id: str,
    ):
        return await self._call(
            "get_account",
            {
                "account_id": account_id,
            },
        )

    async def list_documents(
        self,
        account_id: str,
    ):
        return await self._call(
            "list_account_documents",
            {
                "account_id": account_id,
            },
        )

    async def get_document(
        self,
        account_id: str,
        filename: str,
    ):
        return await self._call(
            "get_account_document",
            {
                "account_id": account_id,
                "filename": filename,
            },
        )

    async def search_documents(
        self,
        query: str,
    ):
        return await self._call(
            "search_documents",
            {
                "query": query,
            },
        )

    async def get_usage(
        self,
        account_id: str,
    ):
        return await self._call(
            "get_account_usage",
            {
                "account_id": account_id,
            },
        )
