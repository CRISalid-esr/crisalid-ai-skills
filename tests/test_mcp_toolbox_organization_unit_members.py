import json
import pytest

ORGANIZATION_UNIT_UID = "local-ru-123456"
PERSON_UID = "local-jdurand@univ-domain.edu"
UNKNOWN_UID = "unknown-org-unit-uid"


@pytest.fixture
async def members_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "get-organization-unit-members")


@pytest.mark.asyncio
async def test_get_organization_unit_members_returns_results(members_tool):
    result = await members_tool.ainvoke({"organization_unit_uid": ORGANIZATION_UNIT_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one result row"


@pytest.mark.asyncio
async def test_get_organization_unit_members_result_structure(members_tool):
    result = await members_tool.ainvoke({"organization_unit_uid": ORGANIZATION_UNIT_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "organization_unit_uid" in row
        assert "members" in row
        assert "member_count" in row


@pytest.mark.asyncio
async def test_get_organization_unit_members_contains_known_person(members_tool):
    result = await members_tool.ainvoke({"organization_unit_uid": ORGANIZATION_UNIT_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0]
    person_uids = [m["person_uid"] for m in row["members"]]
    assert PERSON_UID in person_uids, f"Expected {PERSON_UID} in members: {person_uids}"


@pytest.mark.asyncio
async def test_get_organization_unit_members_has_display_name(members_tool):
    result = await members_tool.ainvoke({"organization_unit_uid": ORGANIZATION_UNIT_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0]
    for member in row["members"]:
        assert "person_name" in member
        assert member["person_name"], "Expected non-empty person_name"


@pytest.mark.asyncio
async def test_get_organization_unit_members_member_count_matches(members_tool):
    result = await members_tool.ainvoke({"organization_unit_uid": ORGANIZATION_UNIT_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0]
    assert row["member_count"] == len(row["members"])


@pytest.mark.asyncio
async def test_get_organization_unit_members_unknown_unit_returns_empty(members_tool):
    result = await members_tool.ainvoke({"organization_unit_uid": UNKNOWN_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert not data, "Expected empty result for unknown organization unit"
