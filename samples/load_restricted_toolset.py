import asyncio

from toolbox_core.protocol import Protocol
from toolbox_langchain import ToolboxClient

TOOLBOX_URL = "http://127.0.0.1:5000"


async def main():
    async with ToolboxClient(TOOLBOX_URL, protocol=Protocol.MCP_LATEST) as toolbox:
        tools = await toolbox.aload_toolset("crisalid-restricted")
        print(f"Loaded {len(tools)} tool(s): {[t.name for t in tools]}")

        schema_tool = next(t for t in tools if t.name == "get-crisalid-schema")
        result = await schema_tool.ainvoke({})
        print(result)


asyncio.run(main())
