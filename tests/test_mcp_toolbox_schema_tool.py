import pytest

EXPECTED_LABELS = {"Person", "Document", "Organisation", "Concept", "Contribution"}


@pytest.mark.asyncio
async def test_schema_tool_returns_known_labels(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    schema_tool = next(t for t in tools if t.name == "get-crisalid-schema")
    result = await schema_tool.ainvoke({})
    for label in EXPECTED_LABELS:
        assert label in result, f"Expected label '{label}' not found in schema output"
