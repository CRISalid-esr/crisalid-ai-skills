"""
Integration tests for SorboBot tools.
"""
import pytest


@pytest.mark.asyncio
async def test_sorbobot_tools_can_be_loaded(sorbobot_tools_dict):
    """Test that all SorboBot tools can be loaded from YAML."""
    expected_tools = {
        "sorbobot-search-domains",
        "sorbobot-get-domain-authors",
        "sorbobot-get-parent-domains",
        "sorbobot-get-person-expertise",
        "sorbobot-execute-cypher-readonly"
    }
    
    tool_names = set(sorbobot_tools_dict.keys())
    assert expected_tools.issubset(tool_names), \
        f"Expected tools {expected_tools}, got {tool_names}"


@pytest.mark.asyncio
async def test_sorbobot_tools_have_cypher_statements(sorbobot_tools_dict):
    """Test that SorboBot cypher tools have valid Cypher statements."""
    # Filter to cypher tools only (not including execute-cypher-readonly which is a different type)
    cypher_tools = {
        name: tool_def for name, tool_def in sorbobot_tools_dict.items()
        if tool_def.get("type") == "neo4j-cypher"
    }
    
    for tool_name, tool_def in cypher_tools.items():
        assert "statement" in tool_def, \
            f"Tool {tool_name} missing 'statement' field"
        assert isinstance(tool_def["statement"], str), \
            f"Tool {tool_name} statement is not a string"
        assert len(tool_def["statement"]) > 0, \
            f"Tool {tool_name} has empty statement"


@pytest.mark.asyncio
async def test_sorbobot_execute_cypher_readonly_exists(sorbobot_tools_dict):
    """Test that sorbobot-execute-cypher-readonly tool exists."""
    tool_def = sorbobot_tools_dict.get("sorbobot-execute-cypher-readonly")
    assert tool_def is not None, \
        "sorbobot-execute-cypher-readonly tool not found"
    # This tool type may not have 'parameters' or 'statement' fields
    # It's a different type of tool, just verify it exists
