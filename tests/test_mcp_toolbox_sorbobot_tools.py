import json

import pytest

# Taxonomy chain: DOMAIN <- FIELD <- SUBFIELD <- TOPIC, plus SIBLING_TOPIC under SUBFIELD (via BROADER)
DOMAIN_UID = "https://openalex.org/domains/3"
FIELD_UID = "https://openalex.org/fields/17"
SUBFIELD_UID = "https://openalex.org/subfields/1702"
TOPIC_UID = "https://openalex.org/T11010"
SIBLING_TOPIC_UID = "https://openalex.org/T10028"

# test-doc-1 (TOPIC, 0.85): Jeannette Durand author, Marc Lefevre thesis director, an external author.
# test-doc-2 (SIBLING_TOPIC, 0.7): Marc Lefevre author.
# test-doc-3 (SIBLING_TOPIC, 0.9): Jeannette Durand jury president only.
PERSON_JDURAND = "test-person-jdurand"
PERSON_MLEFEVRE = "test-person-mlefevre"
PERSON_EXTERNAL = "test-person-external"


async def _call(toolbox_client, name: str, arguments: dict, toolset: str = "sorbobot"):
    """Invoke a tool of the toolset and decode its rows; the toolbox answers JSON null for no row."""
    tools = await toolbox_client.aload_toolset(toolset)
    tool = next(t for t in tools if t.name == name)
    result = await tool.ainvoke(arguments)
    parsed = json.loads(result) if isinstance(result, str) else result
    return [] if parsed is None else parsed


# ── taxonomy ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_concept_hierarchy_runs_from_domain_to_topic(toolbox_client):
    rows = await _call(toolbox_client, "get-concept-hierarchy", {"uids": TOPIC_UID})
    ordered = sorted(rows, key=lambda row: -row["dist"])
    assert [row["ancestor_uid"] for row in ordered] == [DOMAIN_UID, FIELD_UID, SUBFIELD_UID, TOPIC_UID]
    assert [row["ancestor_type"] for row in ordered] == ["Domain", "Field", "SubField", "Topic"]
    assert ordered[-1]["ancestor_name"] == "Logic, Reasoning, and Knowledge"


@pytest.mark.asyncio
async def test_concepts_by_uid_give_labels_and_document_counts(toolbox_client):
    topic = await _call(toolbox_client, "get-concepts-by-uid", {"uids": TOPIC_UID})
    assert topic[0]["name"] == "Logic, Reasoning, and Knowledge"
    assert topic[0]["type"] == "Topic"
    assert topic[0]["description"] == "Logic, reasoning and knowledge representation topic"
    assert topic[0]["nb_docs"] == 1

    domain = await _call(toolbox_client, "get-concepts-by-uid", {"uids": DOMAIN_UID})
    assert domain[0]["nb_docs"] == 3  # every document of the subtree, whatever the role

    strict = await _call(toolbox_client, "get-concepts-by-uid", {"uids": TOPIC_UID, "similarity_threshold": 0.9})
    assert strict[0]["nb_docs"] == 0


@pytest.mark.asyncio
async def test_concept_children_and_siblings(toolbox_client):
    children = await _call(toolbox_client, "list-concept-children", {"uids": SUBFIELD_UID})
    siblings = await _call(toolbox_client, "list-concept-siblings", {"uids": TOPIC_UID})
    assert {row["uid"] for row in children} == {TOPIC_UID, SIBLING_TOPIC_UID}
    assert [row["uid"] for row in siblings] == [SIBLING_TOPIC_UID]
    assert await _call(toolbox_client, "list-concept-children", {"uids": TOPIC_UID}) == []
    assert await _call(toolbox_client, "list-concept-siblings", {"uids": DOMAIN_UID}) == []


@pytest.mark.asyncio
async def test_concept_experts_are_the_internal_authors(toolbox_client):
    """list-concept-experts is shared by the general toolsets, not by sorbobot."""
    rows = await _call(toolbox_client, "list-concept-experts", {"uids": TOPIC_UID}, toolset="crisalid-restricted")
    experts = {row["person_uid"]: row["nb_publications"] for row in rows}
    assert experts == {PERSON_JDURAND: 1, PERSON_MLEFEVRE: 1}


# ── expert evidence ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_expert_evidence_rows(toolbox_client):
    rows = await _call(toolbox_client, "list-concept-expert-evidence", {"uids": TOPIC_UID})
    assert {row["person_uid"] for row in rows} == {PERSON_JDURAND, PERSON_MLEFEVRE}
    row = next(r for r in rows if r["person_uid"] == PERSON_JDURAND)
    assert row["doc_uid"] == "test-doc-1"
    assert row["doc_title"] == "Active Learning Strategies for Knowledge Graphs"
    assert row["publication_date"] == "2020-01-15"
    assert row["topic_uid"] == TOPIC_UID
    assert row["similarity"] == pytest.approx(0.85)


@pytest.mark.asyncio
async def test_expert_evidence_reaches_descendants_and_applies_the_threshold(toolbox_client):
    rows = await _call(toolbox_client, "list-concept-expert-evidence", {"uids": SUBFIELD_UID})
    # test-doc-3 is left out: its only internal contributor presided the jury.
    assert {(row["person_uid"], row["doc_uid"]) for row in rows} == {
        (PERSON_JDURAND, "test-doc-1"),
        (PERSON_MLEFEVRE, "test-doc-1"),
        (PERSON_MLEFEVRE, "test-doc-2"),
    }
    strict = await _call(
        toolbox_client, "list-concept-expert-evidence", {"uids": SUBFIELD_UID, "similarity_threshold": 0.8}
    )
    assert {row["doc_uid"] for row in strict} == {"test-doc-1"}


@pytest.mark.asyncio
async def test_publication_counts_cover_every_domain(toolbox_client):
    rows = await _call(
        toolbox_client,
        "get-person-publication-counts",
        {"person_uids": f"{PERSON_JDURAND},{PERSON_MLEFEVRE},{PERSON_EXTERNAL}"},
    )
    counts = {row["person_uid"]: row["nb_publications_total"] for row in rows}
    assert counts == {PERSON_JDURAND: 1, PERSON_MLEFEVRE: 2}


# ── people ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_person_research_concepts(toolbox_client):
    rows = await _call(toolbox_client, "list-person-research-concepts", {"person_uid": PERSON_MLEFEVRE})
    concepts = {row["domain_uid"]: (row["domain_name"], row["domain_type"], row["nb_publications"]) for row in rows}
    assert concepts == {
        TOPIC_UID: ("Logic, Reasoning, and Knowledge", "Topic", 1),  # thesis direction counts
        SIBLING_TOPIC_UID: ("Topic Modeling", "Topic", 1),
    }


@pytest.mark.asyncio
async def test_person_research_concepts_filters(toolbox_client):
    jury_excluded = await _call(toolbox_client, "list-person-research-concepts", {"person_uid": PERSON_JDURAND})
    strict = await _call(
        toolbox_client,
        "list-person-research-concepts",
        {"person_uid": PERSON_MLEFEVRE, "similarity_threshold": 0.8},
    )
    too_deep = await _call(
        toolbox_client, "list-person-research-concepts", {"person_uid": PERSON_MLEFEVRE, "min_depth": 6}
    )
    assert {row["domain_uid"] for row in jury_excluded} == {TOPIC_UID}
    assert {row["domain_uid"] for row in strict} == {TOPIC_UID}
    assert too_deep == []
    assert await _call(toolbox_client, "list-person-research-concepts", {"person_uid": PERSON_EXTERNAL}) == []


@pytest.mark.asyncio
async def test_person_top_documents_strongest_link_first(toolbox_client):
    rows = await _call(
        toolbox_client,
        "list-person-top-documents",
        {"person_uid": PERSON_MLEFEVRE, "concept_uids": f"{TOPIC_UID},{SIBLING_TOPIC_UID}"},
    )
    assert [row["doc_uid"] for row in rows] == ["test-doc-1", "test-doc-2"]
    assert rows[0]["concept_uids"] == [TOPIC_UID]
    assert rows[0]["roles"] == ["ths"]
    assert rows[0]["best_similarity"] == pytest.approx(0.85)
    assert rows[1]["title"] == "Neural Topic Models for Scientific Corpora"
    assert rows[1]["publication_date"] == "2023"
    assert rows[1]["roles"] == ["aut"]


@pytest.mark.asyncio
async def test_person_top_documents_filters(toolbox_client):
    both_topics = f"{TOPIC_UID},{SIBLING_TOPIC_UID}"
    limited = await _call(
        toolbox_client,
        "list-person-top-documents",
        {"person_uid": PERSON_MLEFEVRE, "concept_uids": both_topics, "limit": 1},
    )
    strict = await _call(
        toolbox_client,
        "list-person-top-documents",
        {"person_uid": PERSON_MLEFEVRE, "concept_uids": both_topics, "similarity_threshold": 0.8},
    )
    only_sibling = await _call(
        toolbox_client, "list-person-top-documents", {"person_uid": PERSON_MLEFEVRE, "concept_uids": SIBLING_TOPIC_UID}
    )
    jury_excluded = await _call(
        toolbox_client, "list-person-top-documents", {"person_uid": PERSON_JDURAND, "concept_uids": SIBLING_TOPIC_UID}
    )
    assert [row["doc_uid"] for row in limited] == ["test-doc-1"]
    assert [row["doc_uid"] for row in strict] == ["test-doc-1"]
    assert [row["doc_uid"] for row in only_sibling] == ["test-doc-2"]
    assert jury_excluded == []


@pytest.mark.asyncio
async def test_document_summaries(toolbox_client):
    rows = await _call(toolbox_client, "list-document-summaries", {"uids": "doc1,test-doc-2", "max_keywords": 2})
    summaries = {row["uid"]: row for row in rows}
    assert summaries["doc1"]["abstract"] == "A detailed abstract of the document in English."
    assert 0 < len(summaries["doc1"]["keywords"]) <= 2
    assert summaries["test-doc-2"] == {"uid": "test-doc-2", "abstract": None, "keywords": []}
