"""
Tests for sorbobot-get-person-expertise tool.
"""
import json
import pytest


@pytest.fixture
async def get_person_expertise_tool(sorbobot_get_person_expertise_tool):
    """Use the fixture from conftest."""
    return sorbobot_get_person_expertise_tool


@pytest.mark.asyncio
async def test_get_person_expertise_returns_results(get_person_expertise_tool):
    """Test that get-person-expertise returns domains for a person."""
    result = await get_person_expertise_tool.ainvoke({
        "name": "Jean",
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert isinstance(data, list), "Expected result to be a list"


@pytest.mark.asyncio
async def test_get_person_expertise_result_structure(get_person_expertise_tool):
    """Test that get-person-expertise results have the expected structure."""
    result = await get_person_expertise_tool.ainvoke({
        "name": "Jean",
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    
    if data:  # Only test structure if we have results
        for row in data:
            assert "uid" in row, "Expected 'uid' field"
            assert "display_name" in row, "Expected 'display_name' field"
            assert "domain_name" in row, "Expected 'domain_name' field"
            assert "domain_path" in row, "Expected 'domain_path' field"
            assert "nb_publications" in row, "Expected 'nb_publications' field"


@pytest.mark.asyncio
async def test_get_person_expertise_respects_limit(get_person_expertise_tool):
    """Test that limit parameter is respected."""
    limit = 3
    result = await get_person_expertise_tool.ainvoke({
        "name": "Jean",
        "limit": limit
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) <= limit, f"Expected at most {limit} results, got {len(data)}"


@pytest.mark.asyncio
async def test_get_person_expertise_partial_name_match(get_person_expertise_tool):
    """Test that partial names match correctly."""
    result = await get_person_expertise_tool.ainvoke({
        "name": "an",  # Partial name that should match many people
        "limit": 5
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert isinstance(data, list), "Expected result to be a list"


@pytest.mark.asyncio
async def test_get_person_expertise_nonexistent_person(get_person_expertise_tool):
    """Test that nonexistent person returns empty results."""
    result = await get_person_expertise_tool.ainvoke({
        "name": "xyznonexistentperson12345xyz",
        "limit": 10
    })
    data = json.loads(result) if isinstance(result, str) else result
    assert data == [], "Expected empty result for nonexistent person"


@pytest.mark.asyncio
async def test_get_person_expertise_case_insensitive(get_person_expertise_tool):
    """Test that name search is case-insensitive."""
    result_lower = await get_person_expertise_tool.ainvoke({
        "name": "jean",
        "limit": 5
    })
    result_upper = await get_person_expertise_tool.ainvoke({
        "name": "JEAN",
        "limit": 5
    })
    
    data_lower = json.loads(result_lower) if isinstance(result_lower, str) else result_lower
    data_upper = json.loads(result_upper) if isinstance(result_upper, str) else result_upper
    
    # Both should return the same number of results
    assert len(data_lower) == len(data_upper), \
        "Case-insensitive search should return same results"
