import json
import pytest

PERSON_UID = "local-jdurand@univ-domain.edu"

# c3 (Wikidata) has both FR and EN pref labels — good for language tests
CONCEPT_UID_BILINGUAL = "http://www.wikidata.org/entity/Q210521"
# c4 — legacy pseudo-concept, no URI, EN pref label only
CONCEPT_UID_LEGACY = "keyword:open-access"


@pytest.fixture
async def concept_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "list-person-concepts")


@pytest.mark.asyncio
async def test_list_person_concepts_returns_results(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data, "Expected at least one concept"


@pytest.mark.asyncio
async def test_list_person_concepts_result_structure(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert "uid" in row
        assert "uri" in row
        assert "pref_labels" in row
        assert "alt_labels" in row
        assert "document_uids" in row


@pytest.mark.asyncio
async def test_list_person_concepts_genuine_concept_has_uri(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    bilingual = next((r for r in data if r["uid"] == CONCEPT_UID_BILINGUAL), None)
    assert bilingual is not None, f"Concept {CONCEPT_UID_BILINGUAL} not found"
    assert bilingual["uri"] == CONCEPT_UID_BILINGUAL


@pytest.mark.asyncio
async def test_list_person_concepts_legacy_concept_no_uri(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    legacy = next((r for r in data if r["uid"] == CONCEPT_UID_LEGACY), None)
    assert legacy is not None, f"Legacy concept {CONCEPT_UID_LEGACY} not found"
    assert legacy["uri"] is None, "Legacy concept should have no URI"


@pytest.mark.asyncio
async def test_list_person_concepts_pref_labels_have_language_tag(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    all_labels = [lbl for row in data for lbl in row.get("pref_labels", [])]
    assert all_labels, "Expected at least one preferred label"
    for lbl in all_labels:
        assert "value" in lbl and "language" in lbl


@pytest.mark.asyncio
async def test_list_person_concepts_pref_labels_default_language_en(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    bilingual = next(r for r in data if r["uid"] == CONCEPT_UID_BILINGUAL)
    languages = {lbl["language"] for lbl in bilingual["pref_labels"]}
    assert "en" in languages, "Expected English pref label when languages defaults to ['en']"
    assert "fr" not in languages, "Should not return French label when only English is requested"


@pytest.mark.asyncio
async def test_list_person_concepts_pref_labels_requested_language_fr(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID, "languages": "fr"})
    data = json.loads(result) if isinstance(result, str) else result
    bilingual = next(r for r in data if r["uid"] == CONCEPT_UID_BILINGUAL)
    languages = {lbl["language"] for lbl in bilingual["pref_labels"]}
    assert "fr" in languages, "Expected French pref label when languages=['fr']"
    assert "en" not in languages, "Should not return English label when only French is requested"


@pytest.mark.asyncio
async def test_list_person_concepts_pref_labels_fallback_to_english(concept_tool):
    # c1 and c2 have only French labels; requesting German should fall back to English,
    # but since there is no English label either, the FR label itself should be returned.
    # c3 has an English label, so requesting German must fall back to English.
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID, "languages": "de"})
    data = json.loads(result) if isinstance(result, str) else result
    bilingual = next(r for r in data if r["uid"] == CONCEPT_UID_BILINGUAL)
    languages = {lbl["language"] for lbl in bilingual["pref_labels"]}
    assert "en" in languages, "c3 should fall back to English pref label when 'de' is not found"


@pytest.mark.asyncio
async def test_list_person_concepts_pref_labels_fallback_all_when_no_english(concept_tool):
    # c1 (Analyse des données) has only a French label; requesting German returns all (FR).
    CONCEPT_UID_FR_ONLY = "http://www.idref.fr/02734004x/id"
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID, "languages": "de"})
    data = json.loads(result) if isinstance(result, str) else result
    fr_only = next((r for r in data if r["uid"] == CONCEPT_UID_FR_ONLY), None)
    assert fr_only is not None
    assert fr_only["pref_labels"], "Should return all available labels (FR) when no EN or DE found"
    assert fr_only["pref_labels"][0]["language"] == "fr"


@pytest.mark.asyncio
async def test_list_person_concepts_no_alt_labels_by_default(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert row["alt_labels"] == [], f"Expected empty alt_labels by default, got {row['alt_labels']}"


@pytest.mark.asyncio
async def test_list_person_concepts_with_alt_labels(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID, "include_alt_labels": 1})
    data = json.loads(result) if isinstance(result, str) else result
    bilingual = next(r for r in data if r["uid"] == CONCEPT_UID_BILINGUAL)
    assert bilingual["alt_labels"], "c3 should have alt labels when include_alt_labels=True"
    for lbl in bilingual["alt_labels"]:
        assert "value" in lbl and "language" in lbl


@pytest.mark.asyncio
async def test_list_person_concepts_custom_limit(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID, "limit": 2})
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) <= 2, f"Expected at most 2 concepts with limit=2, got {len(data)}"


@pytest.mark.asyncio
async def test_list_person_concepts_ul_label_always_returned(concept_tool):
    # c3 has FR, EN, and UL pref labels; requesting French should still return the UL label (as null language)
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID, "languages": "fr"})
    data = json.loads(result) if isinstance(result, str) else result
    bilingual = next(r for r in data if r["uid"] == CONCEPT_UID_BILINGUAL)
    null_lang_labels = [l for l in bilingual["pref_labels"] if l["language"] is None]
    assert null_lang_labels, "Expected at least one pref label with null language (originally 'ul')"


@pytest.mark.asyncio
async def test_list_person_concepts_ul_label_language_is_null(concept_tool):
    # 'ul' tags must be replaced with null — no label should have language == 'ul'
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID, "languages": "de"})
    data = json.loads(result) if isinstance(result, str) else result
    all_labels = [l for row in data for l in row.get("pref_labels", [])]
    assert all(l["language"] != "ul" for l in all_labels), "No label should carry language='ul'"
    bilingual = next(r for r in data if r["uid"] == CONCEPT_UID_BILINGUAL)
    null_lang_labels = [l for l in bilingual["pref_labels"] if l["language"] is None]
    assert null_lang_labels, "Expected the 'ul' label returned as null language on c3"


@pytest.mark.asyncio
async def test_list_person_concepts_document_uids_in_result(concept_tool):
    result = await concept_tool.ainvoke({"person_uid": PERSON_UID})
    data = json.loads(result) if isinstance(result, str) else result
    for row in data:
        assert row["document_uids"], f"Concept {row['uid']} has no document_uids"
        assert "doc1" in row["document_uids"]
