import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from toolbox_core.protocol import Protocol
from toolbox_langchain import ToolboxClient

load_dotenv(Path(__file__).parent / ".env")

TOOLBOX_URL = "http://127.0.0.1:5000"
KEYCLOAK_ISSUER = os.environ["KEYCLOAK_ISSUER"]
KEYCLOAK_CLIENT_ID = os.environ["KEYCLOAK_CLIENT_ID"]
KEYCLOAK_CLIENT_SECRET = os.environ["KEYCLOAK_CLIENT_SECRET"]
KEYCLOAK_SSL_VERIFY = os.environ.get("KEYCLOAK_SSL_VERIFY", "true").lower() != "false"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_BASE_URL = os.environ["OPENAI_BASE_URL"]
OPENAI_MODEL = os.environ["OPENAI_MODEL"]


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
    return response.json()["access_token"]


async def main():
    async with ToolboxClient(TOOLBOX_URL, protocol=Protocol.MCP_LATEST) as toolbox:
        tools = await toolbox.aload_toolset(
            "crisalid-restricted",
            auth_token_getters={"crisalid-keycloak": get_token},
        )
        print(f"Loaded {len(tools)} tool(s): {[t.name for t in tools]}")

        llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
        agent = create_react_agent(llm, tools)

        print("CRISalid agent ready. Type 'exit' to quit.\n")
        history = []
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue

            history.append({"role": "user", "content": user_input})
            result = await agent.ainvoke({"messages": history})
            response = result["messages"][-1].content
            history.append({"role": "assistant", "content": response})
            print(f"\nAgent: {response}\n")


asyncio.run(main())