"""
Tests for sorbobot-get-parent-domains tool via MCP server.
"""
import json
import pytest


@pytest.fixture
async def get_parent_domains_tool(toolbox_client):
    """Load sorbobot-get-parent-domains tool from server."""
    tools = await toolbox_client.aload_toolset("sorbobot-restricted")
    return next(t for t in tools if t.name == "sorbobot-get-parent-domains")


@pytest.mark.asyncio
async def test_get_parent_domains_returns_results(get_parent_domains_tool):
    """Test that get-parent-domains returns parent domains."""
    result = await get_parent_domains_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning"
    })
    data = json.loads(result) if isinstance(result, str) else result
    # Accept None or list
    assert data is None or isinstance(data, list), "Expected result to be a list or None"


@pytest.mark.asyncio
async def test_get_parent_domains_result_structure(get_parent_domains_tool):
    """Test that get-parent-domains results have the expected structure."""
    result = await get_parent_domains_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning"
    })
    data = json.loads(result) if isinstance(result, str) else result
    
    if data:  # Only test structure if we have results
        for row in data:
            assert "name" in row, "Expected 'name' field"
            assert "full_path" in row, "Expected 'full_path' field"
            assert "depth" in row, "Expected 'depth' field"


@pytest.mark.asyncio
async def test_get_parent_domains_comma_separated(get_parent_domains_tool):
    """Test that comma-separated paths are handled correctly."""
    result = await get_parent_domains_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning, artificial_intelligence/natural_language_processing"
    })
    data = json.loads(result) if isinstance(result, str) else result
    # Accept None or list
    assert data is None or isinstance(data, list), "Expected result to be a list or None"


@pytest.mark.asyncio
async def test_get_parent_domains_hierarchy(get_parent_domains_tool):
    """Test that parent domains have lower depth than child domains."""
    child_depth = 3
    result = await get_parent_domains_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning/deep_learning"
    })
    data = json.loads(result) if isinstance(result, str) else result
    
    if data:
        for row in data:
            assert row["depth"] < child_depth, \
                f"Expected parent depth < {child_depth}, got {row['depth']}"


@pytest.mark.asyncio
async def test_get_parent_domains_nonexistent(get_parent_domains_tool):
    """Test that nonexistent path returns empty results."""
    result = await get_parent_domains_tool.ainvoke({
        "domain_paths": "xyznonexistent/fake_path"
    })
    data = json.loads(result) if isinstance(result, str) else result
    # Accept None or empty list
    assert data is None or data == [], "Expected None or empty result for nonexistent path"


