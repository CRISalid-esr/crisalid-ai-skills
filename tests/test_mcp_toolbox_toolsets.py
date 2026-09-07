import pytest

# The concept tools carry no agent prefix: they are shared, so they belong to
# the general toolsets as well as to SorboBot's.
_CONCEPT_TOOLS = {
    "get-concepts-by-uid",
    "get-concept-hierarchy",
    "list-concept-experts",
    "list-person-research-concepts",
}

_CURATED_TOOLS = {
    "get-crisalid-schema",
    "list-person-publications",
    "get-publication",
    "list-person-concepts",
    "search-person-by-name",
    "list-person-collaborators",
    "get-institution-locations",
    "get-person-memberships",
    "search-researchers-by-concept",
    "search-organization-unit-by-name",
    "get-organization-unit-members",
    "publications-by-theme",
} | _CONCEPT_TOOLS


@pytest.mark.asyncio
async def test_restricted_toolset_tools(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    names = set(t.name for t in tools)
    assert names == _CURATED_TOOLS


@pytest.mark.asyncio
async def test_unrestricted_toolset_tools(toolbox_client):
    """Same as restricted, plus raw read-only Cypher."""
    tools = await toolbox_client.aload_toolset("crisalid-unrestricted")
    names = set(t.name for t in tools)
    assert names == _CURATED_TOOLS | {"execute-cypher-readonly"}


@pytest.mark.asyncio
async def test_sorbobot_toolset_tools(toolbox_client):
    """
    SorboBot loads only what it calls.

    It has no ReAct loop: every tool is invoked by name from Python, so a tool
    in this toolset that no code calls is unreachable, not optional.
    """
    tools = await toolbox_client.aload_toolset("sorbobot")
    names = set(t.name for t in tools)
    assert names == _CONCEPT_TOOLS | {"search-person-by-name"}
