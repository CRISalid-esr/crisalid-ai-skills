import json

import pytest

# Taxonomy chain: DOMAIN <- FIELD <- SUBFIELD <- TOPIC (via BROADER)
DOMAIN_UID = "https://openalex.org/domains/3"
FIELD_UID = "https://openalex.org/fields/17"
SUBFIELD_UID = "https://openalex.org/subfields/1702"
TOPIC_UID = "https://openalex.org/T11010"

PERSON_JDURAND = "test-person-jdurand"
PERSON_MLEFEVRE = "test-person-mlefevre"
PERSON_EXTERNAL = "test-person-external"

# From the original (non-taxonomy) fixture — used for the fuzzy name search
# and the top-researchers/top-journals ranking tools.
PERSON_LOCAL_JDURAND = "local-jdurand@univ-domain.edu"
PERSON_LOCAL_JMARTIN = "local-jmartin@univ-domain.edu"


async def _load_tool(toolbox_client, name: str):
    """
    Load the `sorbobot` toolset and return the tool matching `name`.

    Parameters
    ----------
    toolbox_client : ToolboxClient
        Live MCP toolbox client, from the `toolbox_client` fixture.
    name : str
        Name of the tool to retrieve.

    Returns
    -------
    Any
        The matching tool object, ready for `.ainvoke(...)`.
    """
    tools = await toolbox_client.aload_toolset("sorbobot")
    return next(t for t in tools if t.name == name)


def _parse(result):
    """Decode a tool result that may come back as a JSON string or already parsed.

    The toolbox returns JSON `null` — not `[]` — when a query matches zero rows.
    Normalise it exactly as `McpToolboxClient.call` does in production, so the
    tests assert against the shape the agent actually receives.
    """
    parsed = json.loads(result) if isinstance(result, str) else result
    return [] if parsed is None else parsed


# ── get-concept-hierarchy ──────────────────────────────────────────


@pytest.fixture
async def concept_hierarchy_tool(toolbox_client):
    return await _load_tool(toolbox_client, "get-concept-hierarchy")


@pytest.mark.asyncio
async def test_get_concept_hierarchy_full_chain(concept_hierarchy_tool):
    result = await concept_hierarchy_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    assert {row["ancestor_uid"] for row in data} == {
        DOMAIN_UID,
        FIELD_UID,
        SUBFIELD_UID,
        TOPIC_UID,
    }


@pytest.mark.asyncio
async def test_get_concept_hierarchy_ordered_domain_first(concept_hierarchy_tool):
    result = await concept_hierarchy_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    ordered_uids = [row["ancestor_uid"] for row in sorted(data, key=lambda r: -r["dist"])]
    assert ordered_uids == [DOMAIN_UID, FIELD_UID, SUBFIELD_UID, TOPIC_UID]


@pytest.mark.asyncio
async def test_get_concept_hierarchy_types_and_names(concept_hierarchy_tool):
    result = await concept_hierarchy_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    by_uid = {row["ancestor_uid"]: row for row in data}
    assert by_uid[DOMAIN_UID]["ancestor_type"] == "Domain"
    assert by_uid[DOMAIN_UID]["ancestor_name"] == "Physical Sciences"
    assert by_uid[FIELD_UID]["ancestor_type"] == "Field"
    assert by_uid[SUBFIELD_UID]["ancestor_type"] == "SubField"
    assert by_uid[TOPIC_UID]["ancestor_type"] == "Topic"
    assert by_uid[TOPIC_UID]["ancestor_name"] == "Logic, Reasoning, and Knowledge"


@pytest.mark.asyncio
async def test_get_concept_hierarchy_leaf_has_no_descendants_beyond_itself(
    concept_hierarchy_tool,
):
    """Querying the topmost Domain returns only itself (no BROADER above it)."""
    result = await concept_hierarchy_tool.ainvoke({"uids": DOMAIN_UID})
    data = _parse(result)
    assert {row["ancestor_uid"] for row in data} == {DOMAIN_UID}


# ── get-concepts-by-uid ─────────────────────────────────────────────


@pytest.fixture
async def concepts_by_uid_tool(toolbox_client):
    return await _load_tool(toolbox_client, "get-concepts-by-uid")


@pytest.mark.asyncio
async def test_get_concepts_by_uid_returns_name_type_description(concepts_by_uid_tool):
    result = await concepts_by_uid_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    assert len(data) == 1
    assert data[0]["uid"] == TOPIC_UID
    assert data[0]["name"] == "Logic, Reasoning, and Knowledge"
    assert data[0]["type"] == "Topic"
    assert data[0]["description"] == "Logic, reasoning and knowledge representation topic"


@pytest.mark.asyncio
async def test_get_concepts_by_uid_counts_docs_on_topic(concepts_by_uid_tool):
    """Both test-doc-1 and test-doc-1-dup are tagged HAS_TOPIC on the Topic node."""
    result = await concepts_by_uid_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    assert data[0]["nb_docs"] == 2


@pytest.mark.asyncio
async def test_get_concepts_by_uid_aggregates_subtree_docs_from_domain(concepts_by_uid_tool):
    """Querying the top Domain rolls up docs tagged on its descendant Topic."""
    result = await concepts_by_uid_tool.ainvoke({"uids": DOMAIN_UID})
    data = _parse(result)
    assert data[0]["nb_docs"] == 2


@pytest.mark.asyncio
async def test_get_concepts_by_uid_similarity_threshold_excludes_docs(concepts_by_uid_tool):
    """Both HAS_TOPIC edges have similarity=0.85 — a higher threshold excludes them."""
    result = await concepts_by_uid_tool.ainvoke(
        {"uids": TOPIC_UID, "similarity_threshold": 0.9}
    )
    data = _parse(result)
    assert data[0]["nb_docs"] == 0


@pytest.mark.asyncio
async def test_get_concepts_by_uid_multiple_uids(concepts_by_uid_tool):
    result = await concepts_by_uid_tool.ainvoke({"uids": f"{DOMAIN_UID},{TOPIC_UID}"})
    data = _parse(result)
    assert {row["uid"] for row in data} == {DOMAIN_UID, TOPIC_UID}


# ── list-concept-experts ────────────────────────────────────────────


@pytest.fixture
async def concept_experts_tool(toolbox_client):
    return await _load_tool(toolbox_client, "list-concept-experts")


@pytest.mark.asyncio
async def test_list_concept_experts_includes_author_and_thesis_director(concept_experts_tool):
    result = await concept_experts_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    uids = {a["person_uid"] for a in data}
    assert PERSON_JDURAND in uids
    assert PERSON_MLEFEVRE in uids


@pytest.mark.asyncio
async def test_list_concept_experts_excludes_external_person(concept_experts_tool):
    result = await concept_experts_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    uids = {a["person_uid"] for a in data}
    assert PERSON_EXTERNAL not in uids


@pytest.mark.asyncio
async def test_list_concept_experts_excludes_dup_with_plain_author_role(concept_experts_tool):
    """test-doc-1-dup's contribution role is a plain 'AUTHOR' string, not a LOC
    relator URI, so it must not count toward Jeannette Durand's nb_publications
    here (contrast with list-person-research-concepts, which has no
    role filter and does dedupe test-doc-1 / test-doc-1-dup by title+date)."""
    result = await concept_experts_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    jdurand = next(a for a in data if a["person_uid"] == PERSON_JDURAND)
    assert jdurand["nb_publications"] == 1


@pytest.mark.asyncio
async def test_list_concept_experts_searching_from_domain_reaches_topic_docs(
    concept_experts_tool,
):
    """Querying at the top Domain level must still surface experts tagged at
    the descendant Topic level."""
    result = await concept_experts_tool.ainvoke({"uids": DOMAIN_UID})
    data = _parse(result)
    uids = {a["person_uid"] for a in data}
    assert PERSON_JDURAND in uids


@pytest.mark.asyncio
async def test_list_concept_experts_unknown_uid_returns_empty(concept_experts_tool):
    result = await concept_experts_tool.ainvoke({"uids": "https://openalex.org/T99999"})
    data = _parse(result)
    assert data == []


# ── list-person-research-concepts ───────────────────────────────────


@pytest.fixture
async def person_research_concepts_tool(toolbox_client):
    return await _load_tool(toolbox_client, "list-person-research-concepts")


@pytest.mark.asyncio
async def test_list_person_research_concepts_returns_topic(person_research_concepts_tool):
    result = await person_research_concepts_tool.ainvoke({"person_uid": PERSON_JDURAND})
    data = _parse(result)
    assert any(row["domain_uid"] == TOPIC_UID for row in data)


@pytest.mark.asyncio
async def test_list_person_research_concepts_dedupes_harvested_duplicate(
    person_research_concepts_tool,
):
    """test-doc-1 and test-doc-1-dup are the same article (same normalised
    title + publication_date, harvested twice) and must count as a single
    publication, not two."""
    result = await person_research_concepts_tool.ainvoke({"person_uid": PERSON_JDURAND})
    data = _parse(result)
    row = next(r for r in data if r["domain_uid"] == TOPIC_UID)
    assert row["nb_publications"] == 1


@pytest.mark.asyncio
async def test_list_person_research_concepts_min_depth_excludes_domain_level(
    person_research_concepts_tool,
):
    """min_depth defaults to 2 (Domain), so a Topic-level (depth 5) result is
    included by default; raising min_depth above 5 must exclude it."""
    result = await person_research_concepts_tool.ainvoke(
        {"person_uid": PERSON_JDURAND, "min_depth": 6}
    )
    data = _parse(result)
    assert data == []


@pytest.mark.asyncio
async def test_list_person_research_concepts_unknown_person_returns_empty(
    person_research_concepts_tool,
):
    result = await person_research_concepts_tool.ainvoke({"person_uid": "no-such-person"})
    data = _parse(result)
    assert data == []


@pytest.mark.asyncio
async def test_list_person_research_concepts_external_person_excluded(
    person_research_concepts_tool,
):
    """The tool's MATCH filters on Person.external = false — an external uid
    should never resolve to any row."""
    result = await person_research_concepts_tool.ainvoke({"person_uid": PERSON_EXTERNAL})
    data = _parse(result)
    assert data == []


