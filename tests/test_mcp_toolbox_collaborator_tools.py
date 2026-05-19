import json
import pytest

PERSON_UID = "local-jdurand@univ-domain.edu"
COLLABORATOR_UID = "local-jmartin@univ-domain.edu"
DOC_UID = "doc1"


@pytest.fixture
async def collaborator_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "list-person-collaborators")


@pytest.mark.asyncio
async def test_list_person_collaborators_returns_results(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one collaborator"


@pytest.mark.asyncio
async def test_list_person_collaborators_result_structure(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "uid" in row
        assert "display_name" in row
        assert "external" in row
        assert "names" in row
        assert "shared_docs" in row
        assert "affiliations" in row


@pytest.mark.asyncio
async def test_list_person_collaborators_known_collaborator_present(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert COLLABORATOR_UID in uids, f"{COLLABORATOR_UID} not found in collaborators: {uids}"


@pytest.mark.asyncio
async def test_list_person_collaborators_excludes_self(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert PERSON_UID not in uids, "Person should not appear in their own collaborator list"


@pytest.mark.asyncio
async def test_list_person_collaborators_shared_docs_structure(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    collaborator = next(r for r in data if r["uid"] == COLLABORATOR_UID)
    assert collaborator["shared_docs"], "Expected at least one shared document"
    for doc in collaborator["shared_docs"]:
        assert "uid" in doc
        assert "title" in doc
    doc_uids = [d["uid"] for d in collaborator["shared_docs"]]
    assert DOC_UID in doc_uids, f"{DOC_UID} not found in shared docs: {doc_uids}"


@pytest.mark.asyncio
async def test_list_person_collaborators_names_structure(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    collaborator = next(r for r in data if r["uid"] == COLLABORATOR_UID)
    assert collaborator["names"], "Expected at least one name entry"
    for name in collaborator["names"]:
        assert "first_name" in name
        assert "last_name" in name


@pytest.mark.asyncio
async def test_list_person_collaborators_no_affiliations_by_default(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert row["affiliations"] == [], f"Expected empty affiliations by default, got {row['affiliations']}"


@pytest.mark.asyncio
async def test_list_person_collaborators_with_affiliations(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID, "include_affiliations": 1})
    data = json.loads(result) if isinstance(result, str) else result
    collaborator = next(r for r in data if r["uid"] == COLLABORATOR_UID)
    assert collaborator["affiliations"], "Expected affiliations when include_affiliations=1"
    for affil in collaborator["affiliations"]:
        assert "uid" in affil
        assert "display_names" in affil


@pytest.mark.asyncio
async def test_list_person_collaborators_start_date_future_returns_empty(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID, "start_date": "2099-01-01"})
    data = json.loads(result) if isinstance(result, str) else result
    assert data == [], "Expected empty result when start_date is far in the future"


@pytest.mark.asyncio
async def test_list_person_collaborators_end_date_before_publication_returns_empty(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": PERSON_UID, "end_date": "2000-01-01"})
    data = json.loads(result) if isinstance(result, str) else result
    assert data == [], "Expected empty result when end_date is before all publications"


@pytest.mark.asyncio
async def test_list_person_collaborators_unknown_person_returns_empty(collaborator_tool):
    result = await collaborator_tool.ainvoke({"person_uid": "unknown-person-uid"})
    data = json.loads(result) if isinstance(result, str) else result
    assert data == [], "Expected empty result for unknown person uid"
