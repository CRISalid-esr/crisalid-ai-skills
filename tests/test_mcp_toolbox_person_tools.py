import json
import pytest

PERSON_UID = "local-jdurand@univ-domain.edu"
PERSON_DISPLAY_NAME = "Jeannette Durand"


@pytest.fixture
async def person_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "list-person-publications")


@pytest.fixture
async def search_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "search-person-by-name")


@pytest.mark.asyncio
async def test_list_person_publications_returns_documents(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one publication"


@pytest.mark.asyncio
async def test_list_person_publications_has_titles(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert row.get("titles"), f"Document {row.get('uid')} has no titles"


@pytest.mark.asyncio
async def test_list_person_publications_has_abstracts(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    abstracts = [a for row in data for a in row.get("abstracts", [])]
    assert abstracts, "Expected at least one abstract"
    assert all("value" in a and "language" in a for a in abstracts)


@pytest.mark.asyncio
async def test_list_person_publications_has_source_records(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert row.get("source_records"), f"Document {row.get('uid')} has no source records"
        for sr in row["source_records"]:
            assert "harvester" in sr


@pytest.mark.asyncio
async def test_list_person_publications_has_journal(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    channels = [ch for row in data for ch in row.get("publication_channels", [])]
    assert channels, "Expected at least one publication channel with journal info"
    assert all("issn_l" in ch and "labels" in ch for ch in channels)


@pytest.mark.asyncio
async def test_list_person_publications_contributions_structure(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    contributions = [c for row in data for c in row.get("contributions", [])]
    assert contributions, "Expected at least one contribution"
    for c in contributions:
        assert "roles" in c
        assert "affiliations" in c
        assert "person" in c
        assert "uid" in c["person"]


@pytest.mark.asyncio
async def test_search_person_by_name_exact(search_tool):
    result = await search_tool.ainvoke({"name": PERSON_DISPLAY_NAME, "max_results": 5})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one result for exact name"
    uids = [row["uid"] for row in data]
    assert PERSON_UID in uids, f"{PERSON_UID} not found in results: {uids}"


@pytest.mark.asyncio
async def test_search_person_by_name_fuzzy(search_tool):
    result = await search_tool.ainvoke({"name": "Jannete Duran", "max_results": 5})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one result for misspelled name"
    uids = [row["uid"] for row in data]
    assert PERSON_UID in uids, f"{PERSON_UID} not found in fuzzy results: {uids}"


@pytest.mark.asyncio
async def test_search_person_by_name_result_structure(search_tool):
    result = await search_tool.ainvoke({"name": PERSON_DISPLAY_NAME, "max_results": 5})
    data = json.loads(result) if isinstance(result, str) else result
    assert data
    for row in data:
        assert "uid" in row
        assert "display_name" in row
        assert "score" in row
        assert "identifiers" in row
        assert "laboratories" in row


@pytest.mark.asyncio
async def test_search_person_by_name_reversed_order(search_tool):
    result = await search_tool.ainvoke({"name": "Durand Jeannette", "max_results": 5})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert PERSON_UID in uids, f"{PERSON_UID} not found when name is reversed: {uids}"


@pytest.mark.asyncio
async def test_search_person_by_name_last_name_only(search_tool):
    result = await search_tool.ainvoke({"name": "Durand", "max_results": 5})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert PERSON_UID in uids, f"{PERSON_UID} not found when searching by last name only: {uids}"
