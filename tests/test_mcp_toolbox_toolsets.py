import pytest


@pytest.mark.asyncio
async def test_restricted_toolset_tools(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    names = set(t.name for t in tools)
    assert names == {"get-crisalid-schema", "list-person-publications", "get-publication", "list-person-concepts", "search-person-by-name", "list-person-collaborators", "get-institution-locations", "get-person-memberships", "search-researchers-by-concept", "search-organization-unit-by-name", "get-organization-unit-members", "publications-by-theme"}


@pytest.mark.asyncio
async def test_unrestricted_toolset_tools(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-unrestricted")
    names = set(t.name for t in tools)
    assert names == {"get-crisalid-schema", "list-person-publications", "get-publication", "list-person-concepts", "search-person-by-name", "list-person-collaborators", "get-institution-locations", "get-person-memberships", "search-researchers-by-concept", "search-organization-unit-by-name", "get-organization-unit-members", "publications-by-theme", "execute-cypher-readonly"}
