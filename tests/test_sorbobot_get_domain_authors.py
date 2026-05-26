"""
Tests for sorbobot-get-domain-authors tool.
"""
import json
import pytest


@pytest.fixture
async def get_domain_authors_tool(sorbobot_get_domain_authors_tool):
    """Use the fixture from conftest."""
    return sorbobot_get_domain_authors_tool


@pytest.mark.asyncio
async def test_get_domain_authors_returns_results(get_domain_authors_tool):
    """Test that get-domain-authors returns authors for a domain."""
    result = await get_domain_authors_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning",
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert isinstance(data, list), "Expected result to be a list"


@pytest.mark.asyncio
async def test_get_domain_authors_result_structure(get_domain_authors_tool):
    """Test that get-domain-authors results have the expected structure."""
    result = await get_domain_authors_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning",
        "limit": 1
    })
    data = json.loads(result) if isinstance(result, str) else result
    
    if data:  # Only test structure if we have results
        for row in data:
            assert "uid" in row, "Expected 'uid' field"
            assert "display_name" in row, "Expected 'display_name' field"
            assert "nb_publications" in row, "Expected 'nb_publications' field"
            assert "sample_domains" in row, "Expected 'sample_domains' field"
            assert "sample_articles" in row, "Expected 'sample_articles' field"


@pytest.mark.asyncio
async def test_get_domain_authors_respects_limit(get_domain_authors_tool):
    """Test that limit parameter is respected."""
    limit = 2
    result = await get_domain_authors_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning",
        "limit": limit
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) <= limit, f"Expected at most {limit} results, got {len(data)}"


@pytest.mark.asyncio
async def test_get_domain_authors_comma_separated_paths(get_domain_authors_tool):
    """Test that comma-separated domain paths are handled correctly."""
    result = await get_domain_authors_tool.ainvoke({
        "domain_paths": "artificial_intelligence/machine_learning, artificial_intelligence/natural_language_processing",
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert isinstance(data, list), "Expected result to be a list"


@pytest.mark.asyncio
async def test_get_domain_authors_nonexistent_domain(get_domain_authors_tool):
    """Test that nonexistent domain path returns empty results."""
    result = await get_domain_authors_tool.ainvoke({
        "domain_paths": "xyznonexistent/fake_domain_path",
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert data == [], "Expected empty result for nonexistent domain path"
