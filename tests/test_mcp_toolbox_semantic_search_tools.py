import json
import pytest

DOC_UID = "doc1"

# Unit vector along dim 0 — matches title1 (cosine similarity ≈ 1.0)
TITLE_VECTOR = [1.0 if i == 0 else 0.0 for i in range(1024)]
# Unit vector along dim 1 — matches abstract1 (cosine similarity ≈ 1.0)
ABSTRACT_VECTOR = [1.0 if i == 1 else 0.0 for i in range(1024)]


@pytest.fixture
async def semantic_search_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "publications-by-theme")


@pytest.mark.asyncio
async def test_title_search_returns_doc(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "use_abstract": False})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert DOC_UID in uids


@pytest.mark.asyncio
async def test_title_search_result_structure(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "use_abstract": False})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "uid" in row
        assert "score" in row
        assert "titles" in row
        assert isinstance(row["titles"], list)
        assert row["abstracts"] is None


@pytest.mark.asyncio
async def test_abstract_search_returns_doc(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "astrophysics abstract", "semantic_theme_vector": ABSTRACT_VECTOR, "use_abstract": True})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert DOC_UID in uids


@pytest.mark.asyncio
async def test_abstract_search_includes_abstracts(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "astrophysics abstract", "semantic_theme_vector": ABSTRACT_VECTOR, "use_abstract": True})
    data = json.loads(result) if isinstance(result, str) else result
    doc = next(row for row in data if row["uid"] == DOC_UID)
    assert doc["abstracts"] is not None
    assert isinstance(doc["abstracts"], list)
    assert len(doc["abstracts"]) > 0


@pytest.mark.asyncio
async def test_no_duplicate_uids(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "use_abstract": True})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert len(uids) == len(set(uids)), "Duplicate document UIDs in results"


@pytest.mark.asyncio
async def test_limit_is_respected(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "limit": 1})
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) <= 1


@pytest.mark.asyncio
async def test_results_ordered_by_score_descending(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "limit": 10})
    data = json.loads(result) if isinstance(result, str) else result
    scores = [row["score"] for row in data]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_results_include_publication_date(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "limit": 10})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "publication_date" in row


@pytest.mark.asyncio
async def test_internal_only_keeps_internal_contributors_only(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "limit": 10, "internal_only": True})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "internal_only should keep documents with an internal contributor"
    for row in data:
        assert row["contributors"], row["uid"]
        assert all(c["external"] is False for c in row["contributors"]), row["uid"]


@pytest.mark.asyncio
async def test_internal_only_false_keeps_every_contributor(semantic_search_tool):
    strict = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "limit": 10, "internal_only": True})
    loose = await semantic_search_tool.ainvoke({"semantic_theme": "dust in the warm ionized medium", "semantic_theme_vector": TITLE_VECTOR, "limit": 10, "internal_only": False})
    strict_data = json.loads(strict) if isinstance(strict, str) else strict
    loose_data = json.loads(loose) if isinstance(loose, str) else loose
    assert {row["uid"] for row in strict_data} <= {row["uid"] for row in loose_data}
    strict_doc = next(row for row in strict_data if row["uid"] == DOC_UID)
    loose_doc = next(row for row in loose_data if row["uid"] == DOC_UID)
    assert len(loose_doc["contributors"]) >= len(strict_doc["contributors"])


# Unit vector along dim 2 — matches the titles of roles-doc-1 (≈ 1.0) and roles-doc-2 (≈ 0.8)
ROLES_VECTOR = [1.0 if i == 2 else 0.0 for i in range(1024)]
ROLES_DOCS = {"roles-doc-1", "roles-doc-2"}
RELATOR = "http://id.loc.gov/vocabulary/relators/"


async def search_roles_docs(tool, **params) -> dict[str, set[str]]:
    """Contributor uids of the two role fixture documents, keyed by document uid."""
    result = await tool.ainvoke({"semantic_theme": "contribution roles", "semantic_theme_vector": ROLES_VECTOR, "limit": 10, **params})
    data = json.loads(result) if isinstance(result, str) else result
    return {row["uid"]: {c["uid"] for c in row["contributors"]} for row in data or [] if row["uid"] in ROLES_DOCS}


@pytest.mark.asyncio
async def test_empty_roles_keeps_every_contributor(semantic_search_tool):
    default = await search_roles_docs(semantic_search_tool)
    assert await search_roles_docs(semantic_search_tool, roles="") == default
    assert default == {
        "roles-doc-1": {"roles-person-author", "roles-person-advisor", "roles-person-norole", "roles-person-external"},
        "roles-doc-2": {"roles-person-external", "roles-person-advisor"},
    }


@pytest.mark.asyncio
async def test_roles_keeps_authors_only(semantic_search_tool):
    assert await search_roles_docs(semantic_search_tool, roles="aut") == {
        "roles-doc-1": {"roles-person-author", "roles-person-external"},
        "roles-doc-2": {"roles-person-external"},
    }


@pytest.mark.asyncio
async def test_roles_filter_applies_to_every_returned_contributor(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "contribution roles", "semantic_theme_vector": ROLES_VECTOR, "limit": 10, "roles": "aut,ctb"})
    data = json.loads(result) if isinstance(result, str) else result
    assert data
    for row in data:
        assert row["contributors"], row["uid"]
        for contributor in row["contributors"]:
            assert {RELATOR + "aut", RELATOR + "ctb"} & set(contributor["roles"]), row["uid"]


@pytest.mark.asyncio
async def test_roles_matches_any_role_of_a_contribution_and_returns_them_all(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "contribution roles", "semantic_theme_vector": ROLES_VECTOR, "limit": 10, "roles": "dgc"})
    data = json.loads(result) if isinstance(result, str) else result
    assert [row["uid"] for row in data] == ["roles-doc-1"]
    assert data[0]["contributors"] == [{
        "uid": "roles-person-advisor", "name": "Roles Advisor", "external": False,
        "roles": [RELATOR + "ths", RELATOR + "dgc"],
    }]


@pytest.mark.asyncio
@pytest.mark.parametrize("roles", ["ths", " THS ", RELATOR + "ths", "ths,,"])
async def test_roles_are_trimmed_lowercased_and_reduced_from_uris(semantic_search_tool, roles):
    assert await search_roles_docs(semantic_search_tool, roles=roles) == {
        "roles-doc-1": {"roles-person-advisor"},
        "roles-doc-2": {"roles-person-advisor"},
    }


@pytest.mark.asyncio
async def test_roles_and_internal_only_apply_to_the_same_contribution(semantic_search_tool):
    # roles-doc-2 has an internal contributor (advisor) and an author (external), but no internal author
    assert await search_roles_docs(semantic_search_tool, roles="aut", internal_only=True) == {
        "roles-doc-1": {"roles-person-author"},
    }


@pytest.mark.asyncio
async def test_unknown_role_returns_nothing(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme": "contribution roles", "semantic_theme_vector": ROLES_VECTOR, "limit": 10, "roles": "xyz"})
    data = json.loads(result) if isinstance(result, str) else result
    assert not data
