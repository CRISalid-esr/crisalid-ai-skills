import json
import pytest

PERSON_UID = "local-jdurand@univ-domain.edu"
PERSON_DISPLAY_NAME = "Jeannette Durand"
DOC_UID = "doc1"


@pytest.fixture
async def person_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "list-person-publications")


@pytest.fixture
async def publication_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "get-publication")


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
async def test_list_person_publications_has_title(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert row.get("title"), f"Document {row.get('uid')} has no title"


@pytest.mark.asyncio
async def test_list_person_publications_has_uid_and_date(person_tool):
    result = await person_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "uid" in row
        assert "publication_date" in row


@pytest.mark.asyncio
async def test_get_publication_has_titles(publication_tool):
    result = await publication_tool.ainvoke({"uid": DOC_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected a result"
    row = data[0] if isinstance(data, list) else data
    assert row.get("titles"), f"Document {DOC_UID} has no titles"


@pytest.mark.asyncio
async def test_get_publication_has_abstracts(publication_tool):
    result = await publication_tool.ainvoke({"uid": DOC_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0] if isinstance(data, list) else data
    abstracts = row.get("abstracts", [])
    assert abstracts, "Expected at least one abstract"
    assert all("value" in a and "language" in a for a in abstracts)


@pytest.mark.asyncio
async def test_get_publication_has_source_records(publication_tool):
    result = await publication_tool.ainvoke({"uid": DOC_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0] if isinstance(data, list) else data
    assert row.get("source_records"), f"Document {DOC_UID} has no source records"
    for sr in row["source_records"]:
        assert "harvester" in sr


@pytest.mark.asyncio
async def test_get_publication_has_journal(publication_tool):
    result = await publication_tool.ainvoke({"uid": DOC_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0] if isinstance(data, list) else data
    channels = row.get("publication_channels", [])
    assert channels, "Expected at least one publication channel with journal info"
    assert all("issn_l" in ch and "labels" in ch for ch in channels)


@pytest.mark.asyncio
async def test_get_publication_contributions_structure(publication_tool):
    result = await publication_tool.ainvoke({"uid": DOC_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0] if isinstance(data, list) else data
    contributions = row.get("contributions", [])
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
