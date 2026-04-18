import asyncio
import os

import httpx
from toolbox_core.protocol import Protocol
from toolbox_langchain import ToolboxClient

TOOLBOX_URL = "http://127.0.0.1:5000"
KEYCLOAK_ISSUER = os.environ["KEYCLOAK_ISSUER"]
KEYCLOAK_CLIENT_ID = os.environ["KEYCLOAK_CLIENT_ID"]
KEYCLOAK_CLIENT_SECRET = os.environ["KEYCLOAK_CLIENT_SECRET"]
KEYCLOAK_SSL_VERIFY = os.environ.get("KEYCLOAK_SSL_VERIFY", "true").lower() != "false"


def get_token() -> str:
    response = httpx.post(
        f"{KEYCLOAK_ISSUER}/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
        },
        verify=KEYCLOAK_SSL_VERIFY,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print(f"[debug] token fetched: {token}")
    return token


async def main():
    async with ToolboxClient(TOOLBOX_URL, protocol=Protocol.MCP_LATEST) as toolbox:
        tools = await toolbox.aload_toolset(
            "crisalid-restricted",
            auth_token_getters={"crisalid-keycloak": get_token},
        )
        print(f"Loaded {len(tools)} tool(s): {[t.name for t in tools]}")

        schema_tool = next(t for t in tools if t.name == "get-crisalid-schema")
        result = await schema_tool.ainvoke({})
        print(result)


asyncio.run(main())
