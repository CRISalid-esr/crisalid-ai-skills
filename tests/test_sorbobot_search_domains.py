"""
Tests for sorbobot-search-domains tool.
"""
import json
import pytest


DOMAIN_NAME = "machine learning"
SIMILARITY_THRESHOLD = 0.63
MIN_DEPTH = 2


@pytest.fixture
async def search_domains_tool(sorbobot_search_domains_tool):
    """Use the fixture from conftest."""
    return sorbobot_search_domains_tool


@pytest.mark.asyncio
async def test_search_domains_returns_results(search_domains_tool):
    """Test that search-domains returns a list (may be empty if no matching domains in test data)."""
    result = await search_domains_tool.ainvoke({
        "keyword": DOMAIN_NAME,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "min_depth": MIN_DEPTH,
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    # Result can be empty if fixture data doesn't have the domain
    assert isinstance(data, list), "Expected result to be a list"


@pytest.mark.asyncio
async def test_search_domains_result_structure(search_domains_tool):
    """Test that search-domains results have the expected structure."""
    result = await search_domains_tool.ainvoke({
        "keyword": DOMAIN_NAME,
        "limit": 1
    })
    data = json.loads(result) if isinstance(result, str) else result
    
    for row in data:
        assert "name" in row, "Expected 'name' field"
        assert "full_path" in row, "Expected 'full_path' field"
        assert "depth" in row, "Expected 'depth' field"
        assert "nb_docs" in row, "Expected 'nb_docs' field"


@pytest.mark.asyncio
async def test_search_domains_respects_limit(search_domains_tool):
    """Test that limit parameter is respected."""
    limit = 2
    result = await search_domains_tool.ainvoke({
        "keyword": DOMAIN_NAME,
        "limit": limit
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) <= limit, f"Expected at most {limit} results, got {len(data)}"


@pytest.mark.asyncio
async def test_search_domains_respects_min_depth(search_domains_tool):
    """Test that min_depth parameter filters correctly."""
    min_depth = 3
    result = await search_domains_tool.ainvoke({
        "keyword": DOMAIN_NAME,
        "min_depth": min_depth,
        "limit": 100
    })
    data = json.loads(result) if isinstance(result, str) else result
    
    for row in data:
        assert row["depth"] >= min_depth, \
            f"Expected depth >= {min_depth}, got {row['depth']}"


@pytest.mark.asyncio
async def test_search_domains_nonexistent_keyword(search_domains_tool):
    """Test that nonexistent keyword returns empty results."""
    result = await search_domains_tool.ainvoke({
        "keyword": "xyznonexistentdomain12345",
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert data == [], "Expected empty result for nonexistent keyword"
