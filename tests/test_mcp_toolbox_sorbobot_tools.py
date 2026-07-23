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
    """Decode a tool result that may come back as a JSON string or already parsed."""
    return json.loads(result) if isinstance(result, str) else result


# ── sorbobot-get-concept-hierarchy ──────────────────────────────────────────


@pytest.fixture
async def concept_hierarchy_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-get-concept-hierarchy")


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


# ── sorbobot-get-domains-by-uid ─────────────────────────────────────────────


@pytest.fixture
async def domains_by_uid_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-get-domains-by-uid")


@pytest.mark.asyncio
async def test_get_domains_by_uid_returns_name_type_description(domains_by_uid_tool):
    result = await domains_by_uid_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    assert len(data) == 1
    assert data[0]["uid"] == TOPIC_UID
    assert data[0]["name"] == "Logic, Reasoning, and Knowledge"
    assert data[0]["type"] == "Topic"
    assert data[0]["description"] == "Logic, reasoning and knowledge representation topic"


@pytest.mark.asyncio
async def test_get_domains_by_uid_counts_docs_on_topic(domains_by_uid_tool):
    """Both test-doc-1 and test-doc-1-dup are tagged HAS_TOPIC on the Topic node."""
    result = await domains_by_uid_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    assert data[0]["nb_docs"] == 2


@pytest.mark.asyncio
async def test_get_domains_by_uid_aggregates_subtree_docs_from_domain(domains_by_uid_tool):
    """Querying the top Domain rolls up docs tagged on its descendant Topic."""
    result = await domains_by_uid_tool.ainvoke({"uids": DOMAIN_UID})
    data = _parse(result)
    assert data[0]["nb_docs"] == 2


@pytest.mark.asyncio
async def test_get_domains_by_uid_similarity_threshold_excludes_docs(domains_by_uid_tool):
    """Both HAS_TOPIC edges have similarity=0.85 — a higher threshold excludes them."""
    result = await domains_by_uid_tool.ainvoke(
        {"uids": TOPIC_UID, "similarity_threshold": 0.9}
    )
    data = _parse(result)
    assert data[0]["nb_docs"] == 0


@pytest.mark.asyncio
async def test_get_domains_by_uid_multiple_uids(domains_by_uid_tool):
    result = await domains_by_uid_tool.ainvoke({"uids": f"{DOMAIN_UID},{TOPIC_UID}"})
    data = _parse(result)
    assert {row["uid"] for row in data} == {DOMAIN_UID, TOPIC_UID}


# ── sorbobot-get-child-domains / sorbobot-get-parent-domains ────────────────


@pytest.fixture
async def child_domains_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-get-child-domains")


@pytest.fixture
async def parent_domains_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-get-parent-domains")


@pytest.mark.asyncio
async def test_get_child_domains_direct_child(child_domains_tool):
    result = await child_domains_tool.ainvoke({"uids": DOMAIN_UID, "depth_delta": 1})
    data = _parse(result)
    assert {row["uid"] for row in data} == {FIELD_UID}
    assert data[0]["type"] == "Field"


@pytest.mark.asyncio
async def test_get_child_domains_three_levels_down(child_domains_tool):
    result = await child_domains_tool.ainvoke({"uids": DOMAIN_UID, "depth_delta": 3})
    data = _parse(result)
    assert {row["uid"] for row in data} == {TOPIC_UID}


@pytest.mark.asyncio
async def test_get_child_domains_leaf_has_no_children(child_domains_tool):
    result = await child_domains_tool.ainvoke({"uids": TOPIC_UID, "depth_delta": 1})
    data = _parse(result)
    assert data == []


@pytest.mark.asyncio
async def test_get_parent_domains_direct_parent(parent_domains_tool):
    result = await parent_domains_tool.ainvoke({"uids": TOPIC_UID, "depth_delta": 1})
    data = _parse(result)
    assert {row["uid"] for row in data} == {SUBFIELD_UID}
    assert data[0]["type"] == "SubField"


@pytest.mark.asyncio
async def test_get_parent_domains_three_levels_up(parent_domains_tool):
    result = await parent_domains_tool.ainvoke({"uids": TOPIC_UID, "depth_delta": 3})
    data = _parse(result)
    assert {row["uid"] for row in data} == {DOMAIN_UID}


@pytest.mark.asyncio
async def test_get_parent_domains_root_has_no_parent(parent_domains_tool):
    result = await parent_domains_tool.ainvoke({"uids": DOMAIN_UID, "depth_delta": 1})
    data = _parse(result)
    assert data == []


# ── sorbobot-list-domain-experts ────────────────────────────────────────────


@pytest.fixture
async def domain_experts_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-list-domain-experts")


@pytest.mark.asyncio
async def test_list_domain_experts_includes_author_and_thesis_director(domain_experts_tool):
    result = await domain_experts_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    uids = {a["person_uid"] for a in data}
    assert PERSON_JDURAND in uids
    assert PERSON_MLEFEVRE in uids


@pytest.mark.asyncio
async def test_list_domain_experts_excludes_external_person(domain_experts_tool):
    result = await domain_experts_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    uids = {a["person_uid"] for a in data}
    assert PERSON_EXTERNAL not in uids


@pytest.mark.asyncio
async def test_list_domain_experts_excludes_dup_with_plain_author_role(domain_experts_tool):
    """test-doc-1-dup's contribution role is a plain 'AUTHOR' string, not a LOC
    relator URI, so it must not count toward Jeannette Durand's nb_publications
    here (contrast with sorbobot-list-person-research-domains, which has no
    role filter and does dedupe test-doc-1 / test-doc-1-dup by title+date)."""
    result = await domain_experts_tool.ainvoke({"uids": TOPIC_UID})
    data = _parse(result)
    jdurand = next(a for a in data if a["person_uid"] == PERSON_JDURAND)
    assert jdurand["nb_publications"] == 1


@pytest.mark.asyncio
async def test_list_domain_experts_searching_from_domain_reaches_topic_docs(
    domain_experts_tool,
):
    """Querying at the top Domain level must still surface experts tagged at
    the descendant Topic level."""
    result = await domain_experts_tool.ainvoke({"uids": DOMAIN_UID})
    data = _parse(result)
    uids = {a["person_uid"] for a in data}
    assert PERSON_JDURAND in uids


@pytest.mark.asyncio
async def test_list_domain_experts_unknown_uid_returns_empty(domain_experts_tool):
    result = await domain_experts_tool.ainvoke({"uids": "https://openalex.org/T99999"})
    data = _parse(result)
    assert data == []


# ── sorbobot-list-person-research-domains ───────────────────────────────────


@pytest.fixture
async def person_research_domains_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-list-person-research-domains")


@pytest.mark.asyncio
async def test_list_person_research_domains_returns_topic(person_research_domains_tool):
    result = await person_research_domains_tool.ainvoke({"person_uid": PERSON_JDURAND})
    data = _parse(result)
    assert any(row["domain_uid"] == TOPIC_UID for row in data)


@pytest.mark.asyncio
async def test_list_person_research_domains_dedupes_harvested_duplicate(
    person_research_domains_tool,
):
    """test-doc-1 and test-doc-1-dup are the same article (same normalised
    title + publication_date, harvested twice) and must count as a single
    publication, not two."""
    result = await person_research_domains_tool.ainvoke({"person_uid": PERSON_JDURAND})
    data = _parse(result)
    row = next(r for r in data if r["domain_uid"] == TOPIC_UID)
    assert row["nb_publications"] == 1


@pytest.mark.asyncio
async def test_list_person_research_domains_min_depth_excludes_domain_level(
    person_research_domains_tool,
):
    """min_depth defaults to 2 (Domain), so a Topic-level (depth 5) result is
    included by default; raising min_depth above 5 must exclude it."""
    result = await person_research_domains_tool.ainvoke(
        {"person_uid": PERSON_JDURAND, "min_depth": 6}
    )
    data = _parse(result)
    assert data == []


@pytest.mark.asyncio
async def test_list_person_research_domains_unknown_person_returns_empty(
    person_research_domains_tool,
):
    result = await person_research_domains_tool.ainvoke({"person_uid": "no-such-person"})
    data = _parse(result)
    assert data == []


@pytest.mark.asyncio
async def test_list_person_research_domains_external_person_excluded(
    person_research_domains_tool,
):
    """The tool's MATCH filters on Person.external = false — an external uid
    should never resolve to any row."""
    result = await person_research_domains_tool.ainvoke({"person_uid": PERSON_EXTERNAL})
    data = _parse(result)
    assert data == []


# ── sorbobot-search-person-by-name-fuzzy ────────────────────────────────────


@pytest.fixture
async def person_fuzzy_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-search-person-by-name-fuzzy")


@pytest.mark.asyncio
async def test_search_person_by_name_fuzzy_matches_last_name(person_fuzzy_tool):
    result = await person_fuzzy_tool.ainvoke({"name": "Martin"})
    data = _parse(result)
    uids = {row["uid"] for row in data}
    assert PERSON_LOCAL_JMARTIN in uids


@pytest.mark.asyncio
async def test_search_person_by_name_fuzzy_case_insensitive(person_fuzzy_tool):
    result = await person_fuzzy_tool.ainvoke({"name": "martin"})
    data = _parse(result)
    uids = {row["uid"] for row in data}
    assert PERSON_LOCAL_JMARTIN in uids


@pytest.mark.asyncio
async def test_search_person_by_name_fuzzy_full_name(person_fuzzy_tool):
    result = await person_fuzzy_tool.ainvoke({"name": "Jean Martin"})
    data = _parse(result)
    uids = {row["uid"] for row in data}
    assert PERSON_LOCAL_JMARTIN in uids


@pytest.mark.asyncio
async def test_search_person_by_name_fuzzy_excludes_external(person_fuzzy_tool):
    result = await person_fuzzy_tool.ainvoke({"name": "External Researcher"})
    data = _parse(result)
    uids = {row["uid"] for row in data}
    assert PERSON_EXTERNAL not in uids


@pytest.mark.asyncio
async def test_search_person_by_name_fuzzy_ignores_short_words(person_fuzzy_tool):
    """Words of length <= 2 are dropped from the search — a 2-letter query
    alone should not blow up or match everyone."""
    result = await person_fuzzy_tool.ainvoke({"name": "Jo"})
    data = _parse(result)
    assert data == []


@pytest.mark.asyncio
async def test_search_person_by_name_fuzzy_respects_max_results(person_fuzzy_tool):
    result = await person_fuzzy_tool.ainvoke({"name": "Durand", "max_results": 1})
    data = _parse(result)
    assert len(data) <= 1


# ── sorbobot-top-researchers-by-publications ────────────────────────────────


@pytest.fixture
async def top_researchers_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-top-researchers-by-publications")


@pytest.mark.asyncio
async def test_top_researchers_by_publications_includes_known_authors(top_researchers_tool):
    result = await top_researchers_tool.ainvoke({"limit": 50})
    data = _parse(result)
    uids = {row["uid"] for row in data}
    assert PERSON_LOCAL_JDURAND in uids
    assert PERSON_LOCAL_JMARTIN in uids


@pytest.mark.asyncio
async def test_top_researchers_by_publications_respects_limit(top_researchers_tool):
    result = await top_researchers_tool.ainvoke({"limit": 1})
    data = _parse(result)
    assert len(data) <= 1


@pytest.mark.asyncio
async def test_top_researchers_by_publications_sorted_descending(top_researchers_tool):
    result = await top_researchers_tool.ainvoke({"limit": 50})
    data = _parse(result)
    counts = [row["nb_publications"] for row in data]
    assert counts == sorted(counts, reverse=True)


# ── sorbobot-top-journals-by-articles ───────────────────────────────────────


@pytest.fixture
async def top_journals_tool(toolbox_client):
    return await _load_tool(toolbox_client, "sorbobot-top-journals-by-articles")


@pytest.mark.asyncio
async def test_top_journals_by_articles_includes_known_journal(top_journals_tool):
    result = await top_journals_tool.ainvoke({"limit": 50})
    data = _parse(result)
    uids = {row["uid"] for row in data}
    assert "journal-0004-637X" in uids


@pytest.mark.asyncio
async def test_top_journals_by_articles_article_count(top_journals_tool):
    result = await top_journals_tool.ainvoke({"limit": 50})
    data = _parse(result)
    row = next(r for r in data if r["uid"] == "journal-0004-637X")
    assert row["nb_articles"] == 1


@pytest.mark.asyncio
async def test_top_journals_by_articles_respects_limit(top_journals_tool):
    result = await top_journals_tool.ainvoke({"limit": 1})
    data = _parse(result)
    assert len(data) <= 1
