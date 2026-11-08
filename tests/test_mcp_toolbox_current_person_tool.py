import json
import pytest

# Jeannette Durand: the fixture stores her `local` identifier as a full eppn.
EPPN_AS_STORED = "jdurand@univ-domain.edu"
PERSON_UID = "local-jdurand@univ-domain.edu"
RESEARCH_UNIT_UID = "local-ru-123456"
# Jean Martin: bare `local` login in the fixture, resolved from an eppn.
BARE_LOGIN = "jmartin"
BARE_LOGIN_EPPN = "jmartin@univ-domain.edu"
COLLABORATOR_UID = "local-jmartin@univ-domain.edu"
UNKNOWN_LOGIN = "nobody@univ-domain.edu"


@pytest.fixture
async def current_person_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "get-current-person")


def _rows(result):
    return json.loads(result) if isinstance(result, str) else result


@pytest.mark.asyncio
async def test_get_current_person_matches_stored_eppn(current_person_tool):
    data = _rows(await current_person_tool.ainvoke({"username": EPPN_AS_STORED}))
    assert len(data) == 1
    assert data[0]["uid"] == PERSON_UID


@pytest.mark.asyncio
async def test_get_current_person_strips_eppn_domain(current_person_tool):
    data = _rows(await current_person_tool.ainvoke({"username": BARE_LOGIN_EPPN}))
    assert [row["uid"] for row in data] == [COLLABORATOR_UID]


@pytest.mark.asyncio
async def test_get_current_person_accepts_bare_login(current_person_tool):
    data = _rows(await current_person_tool.ainvoke({"username": BARE_LOGIN}))
    assert [row["uid"] for row in data] == [COLLABORATOR_UID]


@pytest.mark.asyncio
async def test_get_current_person_result_shape(current_person_tool):
    data = _rows(await current_person_tool.ainvoke({"username": EPPN_AS_STORED}))
    row = data[0]
    assert row["display_name"] == "Jeannette Durand"
    assert row["external"] is False
    assert {"type": "local", "value": EPPN_AS_STORED} in row["identifiers"]
    assert {"type": "orcid", "value": "0000-0001-2345-6789"} in row["identifiers"]
    lab = next(lab for lab in row["laboratories"] if lab["uid"] == RESEARCH_UNIT_UID)
    assert "LRA" in lab["short_labels"]
    assert lab["long_labels"]


@pytest.mark.asyncio
async def test_get_current_person_unknown_login_is_empty(current_person_tool):
    data = _rows(await current_person_tool.ainvoke({"username": UNKNOWN_LOGIN}))
    assert data == []
