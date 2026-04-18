import pytest


@pytest.fixture
async def cypher_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-unrestricted")
    return next(t for t in tools if t.name == "execute-cypher-readonly")


@pytest.mark.asyncio
async def test_count_persons(cypher_tool):
    result = await cypher_tool.ainvoke(
        {"cypher": "MATCH (n:Person) RETURN count(n) AS count"}
    )
    assert "1" in str(result)


@pytest.mark.asyncio
async def test_count_documents(cypher_tool):
    result = await cypher_tool.ainvoke(
        {"cypher": "MATCH (n:Document) RETURN count(n) AS count"}
    )
    assert "1" in str(result)


@pytest.mark.asyncio
async def test_person_has_identifiers(cypher_tool):
    result = await cypher_tool.ainvoke(
        {"cypher": "MATCH (p:Person)-[:HAS_IDENTIFIER]->(i) RETURN i LIMIT 5"}
    )
    assert result and str(result).strip() not in ("", "[]", "null")
