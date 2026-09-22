import pytest

# The concept tools carry no agent prefix: they are shared, so they belong to
# the general toolsets as well as to SorboBot's.
_CONCEPT_TOOLS = {
    "get-concepts-by-uid",
    "get-concept-hierarchy",
    "get-person-publication-counts",
    "list-concept-experts",
    "list-concept-children",
    "list-concept-siblings",
    "list-concept-expert-evidence",
    "list-person-research-concepts",
    "list-person-top-documents",
    "list-document-summaries",
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
    """SorboBot loads only what it calls."""
    tools = await toolbox_client.aload_toolset("sorbobot")
    names = set(t.name for t in tools)
    assert names == (_CONCEPT_TOOLS - {"list-concept-experts"}) | {"search-person-by-name"}
