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
    result = await semantic_search_tool.ainvoke({"semantic_theme_vector": TITLE_VECTOR, "use_abstract": False})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert DOC_UID in uids


@pytest.mark.asyncio
async def test_title_search_result_structure(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme_vector": TITLE_VECTOR, "use_abstract": False})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "uid" in row
        assert "score" in row
        assert "titles" in row
        assert isinstance(row["titles"], list)
        assert row["abstracts"] is None


@pytest.mark.asyncio
async def test_abstract_search_returns_doc(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme_vector": ABSTRACT_VECTOR, "use_abstract": True})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert DOC_UID in uids


@pytest.mark.asyncio
async def test_abstract_search_includes_abstracts(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme_vector": ABSTRACT_VECTOR, "use_abstract": True})
    data = json.loads(result) if isinstance(result, str) else result
    doc = next(row for row in data if row["uid"] == DOC_UID)
    assert doc["abstracts"] is not None
    assert isinstance(doc["abstracts"], list)
    assert len(doc["abstracts"]) > 0


@pytest.mark.asyncio
async def test_no_duplicate_uids(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme_vector": TITLE_VECTOR, "use_abstract": True})
    data = json.loads(result) if isinstance(result, str) else result
    uids = [row["uid"] for row in data]
    assert len(uids) == len(set(uids)), "Duplicate document UIDs in results"


@pytest.mark.asyncio
async def test_limit_is_respected(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme_vector": TITLE_VECTOR, "limit": 1})
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) <= 1


@pytest.mark.asyncio
async def test_results_ordered_by_score_descending(semantic_search_tool):
    result = await semantic_search_tool.ainvoke({"semantic_theme_vector": TITLE_VECTOR, "limit": 10})
    data = json.loads(result) if isinstance(result, str) else result
    scores = [row["score"] for row in data]
    assert scores == sorted(scores, reverse=True)
