import asyncio

from toolbox_core.protocol import Protocol
from toolbox_langchain import ToolboxClient

TOOLBOX_URL = "http://127.0.0.1:5000"
SAMPLE_QUERY = "MATCH (n) RETURN labels(n) AS label, count(n) AS count ORDER BY count DESC LIMIT 10"


async def main():
    async with ToolboxClient(TOOLBOX_URL, protocol=Protocol.MCP_LATEST) as toolbox:
        tools = await toolbox.aload_toolset("crisalid-unrestricted")
        print(f"Loaded {len(tools)} tool(s): {[t.name for t in tools]}")

        cypher_tool = next(t for t in tools if t.name == "execute-cypher-readonly")
        result = await cypher_tool.ainvoke({"cypher": SAMPLE_QUERY})
        print(result)


asyncio.run(main())
