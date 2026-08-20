import json
from pathlib import Path

from mcp.server import MCPServer




BASE_DIR = Path(__file__).parent / "data" / "accounts"

mcp = MCPServer("GTM Intelligence SOR")


def account_dir(account_id: str) -> Path:
    path = BASE_DIR / account_id

    if not path.exists():
        raise ValueError(f"Unknown account: {account_id}")

    return path


@mcp.tool()
def list_accounts() -> list[dict]:
    """List all accounts in the Book of Business."""

    accounts = []

    for directory in sorted(BASE_DIR.iterdir()):
        if not directory.is_dir():
            continue

        profile_path = directory / "profile.json"

        if not profile_path.exists():
            continue

        with profile_path.open() as f:
            accounts.append(json.load(f))

    return accounts


@mcp.tool()
def get_account(account_id: str) -> dict:
    """Get account profile."""

    path = account_dir(account_id) / "profile.json"

    with path.open() as f:
        return json.load(f)


@mcp.tool()
def list_account_documents(account_id: str) -> list[dict]:
    """List documents belonging to an account."""

    documents_dir = account_dir(account_id) / "documents"

    documents = []

    for path in sorted(documents_dir.glob("*")):
        if path.is_file():
            documents.append(
                {
                    "file": path.name,
                    "account_id": account_id,
                }
            )

    return documents


@mcp.tool()
def get_account_document(
    account_id: str,
    filename: str,
) -> dict:
    """Retrieve one account document."""

    path = account_dir(account_id) / "documents" / filename

    if not path.exists():
        raise ValueError(
            f"Document not found: {filename}"
        )

    return {
        "account_id": account_id,
        "file": filename,
        "content": path.read_text(),
    }


@mcp.tool()
def get_account_usage(account_id: str) -> dict:
    """Retrieve account usage."""

    path = account_dir(account_id) / "usage.json"

    if not path.exists():
        raise ValueError(
            f"Usage data not found for {account_id}"
        )

    with path.open() as f:
        return json.load(f)


@mcp.tool()
def search_documents(query: str) -> list[dict]:
    """Search account documents by text."""

    query = query.lower()
    results = []

    for account in BASE_DIR.iterdir():

        documents_dir = account / "documents"

        if not documents_dir.exists():
            continue

        for path in documents_dir.glob("*"):

            if not path.is_file():
                continue

            content = path.read_text()

            if query in content.lower():

                results.append(
                    {
                        "account_id": account.name,
                        "file": path.name,
                        "content": content,
                    }
                )

    return results


if __name__ == "__main__":
    mcp.run()
