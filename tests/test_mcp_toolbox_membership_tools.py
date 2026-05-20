import json
import pytest

PERSON_UID = "local-jdurand@univ-domain.edu"
RESEARCH_UNIT_UID = "local-ru-123456"
UNKNOWN_UID = "unknown-person-uid"


@pytest.fixture
async def membership_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "get-person-memberships")


@pytest.mark.asyncio
async def test_get_person_memberships_returns_results(membership_tool):
    result = await membership_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one membership"


@pytest.mark.asyncio
async def test_get_person_memberships_result_structure(membership_tool):
    result = await membership_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "institution_uid" in row
        assert "long_labels" in row
        assert "short_labels" in row


@pytest.mark.asyncio
async def test_get_person_memberships_contains_research_unit(membership_tool):
    result = await membership_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["institution_uid"] for row in data]
    assert RESEARCH_UNIT_UID in uids, f"Expected {RESEARCH_UNIT_UID} in memberships: {uids}"


@pytest.mark.asyncio
async def test_get_person_memberships_has_long_label(membership_tool):
    result = await membership_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    ru = next(row for row in data if row["institution_uid"] == RESEARCH_UNIT_UID)
    assert ru["long_labels"], "Expected at least one long label for the research unit"
    for label in ru["long_labels"]:
        assert "value" in label
        assert "language" in label


@pytest.mark.asyncio
async def test_get_person_memberships_has_short_label(membership_tool):
    result = await membership_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    ru = next(row for row in data if row["institution_uid"] == RESEARCH_UNIT_UID)
    assert ru["short_labels"], "Expected at least one short label for the research unit"
    short_values = [label["value"] for label in ru["short_labels"]]
    assert "LRA" in short_values


@pytest.mark.asyncio
async def test_get_person_memberships_unknown_person_returns_empty(membership_tool):
    result = await membership_tool.ainvoke({"person_uid": UNKNOWN_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert not data, "Expected empty result for unknown person"
