import asyncio
import os

import httpx
from toolbox_core.protocol import Protocol
from toolbox_langchain import ToolboxClient

# Delegated-token sample: the toolbox is called with the token of a signed-in
# person (as the crisalid-agents chat API does), not with a service account.
#
# USER_ACCESS_TOKEN is an access token obtained by a user through a Keycloak
# client (sovisuplus, open-webui...). When KEYCLOAK_CLIENT_ID is set, it is
# exchanged (RFC 8693, Keycloak standard token exchange) for a token whose
# audience is the toolbox (MCP_AUDIENCE); otherwise it is sent as is, which
# only works if its `aud` already contains the toolbox audience.
TOOLBOX_URL = "http://127.0.0.1:5000"
USER_ACCESS_TOKEN = os.environ["USER_ACCESS_TOKEN"]
KEYCLOAK_ISSUER = os.environ.get("KEYCLOAK_ISSUER")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")
KEYCLOAK_SSL_VERIFY = os.environ.get("KEYCLOAK_SSL_VERIFY", "true").lower() != "false"
MCP_AUDIENCE = os.environ.get("MCP_AUDIENCE", "crisalid-graph-mcp")


def exchange_token(subject_token: str) -> str:
    response = httpx.post(
        f"{KEYCLOAK_ISSUER}/protocol/openid-connect/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "subject_token": subject_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "audience": MCP_AUDIENCE,
        },
        verify=KEYCLOAK_SSL_VERIFY,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print(f"[debug] token exchanged for audience {MCP_AUDIENCE}: {token}")
    return token


async def main():
    if KEYCLOAK_CLIENT_ID:
        token = exchange_token(USER_ACCESS_TOKEN)
    else:
        token = USER_ACCESS_TOKEN
        print("[debug] KEYCLOAK_CLIENT_ID not set: sending the user token as is")

    async with ToolboxClient(TOOLBOX_URL, protocol=Protocol.MCP_LATEST) as toolbox:
        tools = await toolbox.aload_toolset(
            "crisalid-restricted",
            auth_token_getters={"crisalid-keycloak": lambda: token},
        )
        print(f"Loaded {len(tools)} tool(s): {[t.name for t in tools]}")

        # No argument: the login comes from the preferred_username claim of the token.
        current_person_tool = next(t for t in tools if t.name == "get-current-person")
        result = await current_person_tool.ainvoke({})
        print(result)


asyncio.run(main())
