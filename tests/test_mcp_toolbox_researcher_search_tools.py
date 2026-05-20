import json
import pytest

PERSON_UID = "local-jdurand@univ-domain.edu"
PERSON_NAME = "Jeannette Durand"

# "analyse" is a substring of "Analyse des données" (concept c1 pref label, fr)
CONCEPT_PREF_LABEL_FRAGMENT = "analyse"
# "milieu" is a substring of "Milieu interstellaire" (concept c2 alt label, fr)
CONCEPT_ALT_LABEL_FRAGMENT = "milieu"
# concept that exists in no label
UNKNOWN_CONCEPT = "xyznonexistentconcept"


@pytest.fixture
async def researcher_search_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "search-researchers-by-concept")


@pytest.mark.asyncio
async def test_search_researchers_by_concept_returns_results(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one researcher"


@pytest.mark.asyncio
async def test_search_researchers_by_concept_result_structure(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "researcher_uid" in row
        assert "researcher_name" in row
        assert "publication_titles" in row
        assert "publication_count" in row


@pytest.mark.asyncio
async def test_search_researchers_by_concept_contains_known_researcher(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["researcher_uid"] for row in data]
    assert PERSON_UID in uids, f"Expected {PERSON_UID} in results: {uids}"


@pytest.mark.asyncio
async def test_search_researchers_by_concept_has_publication_titles(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT})
    data = json.loads(result) if isinstance(result, str) else result
    researcher = next(row for row in data if row["researcher_uid"] == PERSON_UID)
    assert researcher["publication_titles"], "Expected at least one publication title"
    assert isinstance(researcher["publication_titles"], list)


@pytest.mark.asyncio
async def test_search_researchers_by_concept_publication_count_matches_titles(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert row["publication_count"] == len(row["publication_titles"])


@pytest.mark.asyncio
async def test_search_researchers_by_concept_case_insensitive(researcher_search_tool):
    result_lower = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT})
    result_upper = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT.upper()})
    data_lower = json.loads(result_lower) if isinstance(result_lower, str) else result_lower
    data_upper = json.loads(result_upper) if isinstance(result_upper, str) else result_upper
    uids_lower = {row["researcher_uid"] for row in data_lower}
    uids_upper = {row["researcher_uid"] for row in data_upper}
    assert uids_lower == uids_upper, "Case should not affect results"


@pytest.mark.asyncio
async def test_search_researchers_by_concept_matches_alt_labels(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": CONCEPT_ALT_LABEL_FRAGMENT})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, f"Expected results when matching alt label fragment '{CONCEPT_ALT_LABEL_FRAGMENT}'"
    uids = [row["researcher_uid"] for row in data]
    assert PERSON_UID in uids


@pytest.mark.asyncio
async def test_search_researchers_by_concept_ordered_by_count(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": CONCEPT_PREF_LABEL_FRAGMENT})
    data = json.loads(result) if isinstance(result, str) else result
    counts = [row["publication_count"] for row in data]
    assert counts == sorted(counts, reverse=True), "Results should be ordered by publication_count descending"


@pytest.mark.asyncio
async def test_search_researchers_by_concept_unknown_returns_empty(researcher_search_tool):
    result = await researcher_search_tool.ainvoke({"concept": UNKNOWN_CONCEPT})
    data = json.loads(result) if isinstance(result, str) else result
    assert not data, "Expected empty result for unknown concept"
