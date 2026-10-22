import json
import pytest

ORGANIZATION_UNIT_UID = "local-ru-123456"
PERSON_UID = "local-jdurand@univ-domain.edu"
PERSON_ORCID = "0000-0001-2345-6789"
UNKNOWN_UID = "unknown-org-unit-uid"


@pytest.fixture
async def count_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(
        t for t in tools if t.name == "count-organization-unit-members-with-identifier"
    )


def _row(result):
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one result row"
    return data[0]


@pytest.mark.asyncio
async def test_result_structure(count_tool):
    result = await count_tool.ainvoke(
        {"organization_unit_uid": ORGANIZATION_UNIT_UID, "identifier_type": "orcid"}
    )
    row = _row(result)
    for key in (
        "organization_unit_uid",
        "identifier_type",
        "member_count",
        "with_identifier_count",
        "without_identifier_count",
        "percent_with_identifier",
        "members_with_identifier",
        "members_without_identifier",
    ):
        assert key in row, f"Expected key {key} in {row}"


@pytest.mark.asyncio
async def test_orcid_counts_are_consistent(count_tool):
    result = await count_tool.ainvoke(
        {"organization_unit_uid": ORGANIZATION_UNIT_UID, "identifier_type": "orcid"}
    )
    row = _row(result)
    assert row["with_identifier_count"] + row["without_identifier_count"] == row["member_count"]
    assert row["with_identifier_count"] == len(row["members_with_identifier"])
    assert row["without_identifier_count"] == len(row["members_without_identifier"])


@pytest.mark.asyncio
async def test_percent_matches_counts(count_tool):
    result = await count_tool.ainvoke(
        {"organization_unit_uid": ORGANIZATION_UNIT_UID, "identifier_type": "orcid"}
    )
    row = _row(result)
    expected = round(100.0 * row["with_identifier_count"] / row["member_count"], 1)
    assert row["percent_with_identifier"] == pytest.approx(expected)


@pytest.mark.asyncio
async def test_member_with_orcid_is_listed_with_value(count_tool):
    result = await count_tool.ainvoke(
        {"organization_unit_uid": ORGANIZATION_UNIT_UID, "identifier_type": "orcid"}
    )
    row = _row(result)
    by_uid = {m["person_uid"]: m for m in row["members_with_identifier"]}
    assert PERSON_UID in by_uid, f"Expected {PERSON_UID} among ORCID holders"
    assert PERSON_ORCID in by_uid[PERSON_UID]["identifier_values"]
    assert by_uid[PERSON_UID]["person_name"], "Expected non-empty person_name"


@pytest.mark.asyncio
async def test_identifier_type_defaults_to_orcid(count_tool):
    # identifier_type omitted -> defaults to 'orcid'
    result = await count_tool.ainvoke({"organization_unit_uid": ORGANIZATION_UNIT_UID})
    row = _row(result)
    assert row["identifier_type"] == "orcid"
    assert PERSON_UID in {m["person_uid"] for m in row["members_with_identifier"]}


@pytest.mark.asyncio
async def test_missing_identifier_type_puts_member_in_without_group(count_tool):
    # No fixture member carries a 'scopus' identifier.
    result = await count_tool.ainvoke(
        {"organization_unit_uid": ORGANIZATION_UNIT_UID, "identifier_type": "scopus"}
    )
    row = _row(result)
    assert row["with_identifier_count"] == 0
    assert row["percent_with_identifier"] == 0.0
    assert PERSON_UID in {m["person_uid"] for m in row["members_without_identifier"]}


@pytest.mark.asyncio
async def test_unknown_unit_returns_empty(count_tool):
    result = await count_tool.ainvoke(
        {"organization_unit_uid": UNKNOWN_UID, "identifier_type": "orcid"}
    )
    data = json.loads(result) if isinstance(result, str) else result
    assert not data, "Expected empty result for unknown organization unit"
