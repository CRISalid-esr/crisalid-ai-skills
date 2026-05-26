"""
Integration tests for SorboBot tools via MCP server.
"""
import json
import pytest


@pytest.mark.asyncio
async def test_sorbobot_toolset_restricted_loads(toolbox_client):
    """Test that sorbobot-restricted toolset can be loaded."""
    tools = await toolbox_client.aload_toolset("sorbobot-restricted")
    assert len(tools) == 4, "sorbobot-restricted should have 4 tools"
    tool_names = {t.name for t in tools}
    expected = {
        "sorbobot-search-domains",
        "sorbobot-get-domain-authors",
        "sorbobot-get-parent-domains",
        "sorbobot-get-person-expertise"
    }
    assert expected == tool_names, f"Expected {expected}, got {tool_names}"


@pytest.mark.asyncio
async def test_sorbobot_toolset_full_loads(toolbox_client):
    """Test that sorbobot-full toolset can be loaded."""
    tools = await toolbox_client.aload_toolset("sorbobot-full")
    assert len(tools) == 5, "sorbobot-full should have 5 tools"
    tool_names = {t.name for t in tools}
    expected = {
        "sorbobot-search-domains",
        "sorbobot-get-domain-authors",
        "sorbobot-get-parent-domains",
        "sorbobot-get-person-expertise",
        "sorbobot-execute-cypher-readonly"
    }
    assert expected == tool_names, f"Expected {expected}, got {tool_names}"


@pytest.mark.asyncio
async def test_sorbobot_search_domains_tool_callable(toolbox_client):
    """Test that sorbobot-search-domains tool is callable."""
    tools = await toolbox_client.aload_toolset("sorbobot-restricted")
    tool = next(t for t in tools if t.name == "sorbobot-search-domains")
    
    result = await tool.ainvoke({"keyword": "test", "limit": 1})
    data = json.loads(result) if isinstance(result, str) else result
    
    # Accept None or list (no results in test fixture)
    assert data is None or isinstance(data, list), "Tool should return a list or None"


