import json
import pytest

RESEARCH_UNIT_UID = "local-ru-123456"
INSTITUTION_UID = "local-inst-234567"


@pytest.fixture
async def org_search_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "search-organization-unit-by-name")


@pytest.mark.asyncio
async def test_search_by_long_label(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "laboratoire"})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert RESEARCH_UNIT_UID in uids


@pytest.mark.asyncio
async def test_search_by_short_label(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "lra"})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert RESEARCH_UNIT_UID in uids


@pytest.mark.asyncio
async def test_result_structure(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "laboratoire"})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "uid" in row
        assert "long_label" in row
        assert "type" in row
        assert "parent" in row
        assert "children" in row


@pytest.mark.asyncio
async def test_generic_type_returned(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "laboratoire"})
    data = json.loads(result) if isinstance(result, str) else result
    unit = next(row for row in data if row["uid"] == RESEARCH_UNIT_UID)
    assert unit["type"] == "unit"


@pytest.mark.asyncio
async def test_no_parent_by_default(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "laboratoire"})
    data = json.loads(result) if isinstance(result, str) else result
    unit = next(row for row in data if row["uid"] == RESEARCH_UNIT_UID)
    assert unit["parent"] is None


@pytest.mark.asyncio
async def test_include_parent(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "laboratoire", "include_parent": 1})
    data = json.loads(result) if isinstance(result, str) else result
    unit = next(row for row in data if row["uid"] == RESEARCH_UNIT_UID)
    assert unit["parent"] is not None
    assert unit["parent"]["uid"] == INSTITUTION_UID


@pytest.mark.asyncio
async def test_include_children(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "université", "include_children": 1})
    data = json.loads(result) if isinstance(result, str) else result
    institution = next(row for row in data if row["uid"] == INSTITUTION_UID)
    child_uids = [c["uid"] for c in institution["children"]]
    assert RESEARCH_UNIT_UID in child_uids


@pytest.mark.asyncio
async def test_no_children_by_default(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "université"})
    data = json.loads(result) if isinstance(result, str) else result
    institution = next(row for row in data if row["uid"] == INSTITUTION_UID)
    assert institution["children"] == []


@pytest.mark.asyncio
async def test_unknown_name_returns_empty(org_search_tool):
    result = await org_search_tool.ainvoke({"name": "xyznonexistentorg42"})
    data = json.loads(result) if isinstance(result, str) else result
    assert not data
