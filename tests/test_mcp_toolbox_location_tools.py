import json
import pytest

STATE_UID = "ao-state-1"
ROOT_UID = "ao-root-1"
STATE_NO_LOCATION_UID = "ao-state-2"


@pytest.fixture
async def location_tool(toolbox_client):
    tools = await toolbox_client.aload_toolset("crisalid-restricted")
    return next(t for t in tools if t.name == "get-institution-locations")


@pytest.mark.asyncio
async def test_get_institution_locations_single_uid_returns_one_entry(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) == 1, f"Expected exactly one entry for a single UID, got {len(data)}"


@pytest.mark.asyncio
async def test_get_institution_locations_result_structure(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    row = data[0]
    assert "uid" in row
    assert "display_names" in row
    assert "coordinates" in row
    assert "addresses" in row


@pytest.mark.asyncio
async def test_get_institution_locations_uid_echoed(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data[0]["uid"] == STATE_UID


@pytest.mark.asyncio
async def test_get_institution_locations_state_has_coordinates(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    coords = data[0]["coordinates"]
    assert coords, f"Expected coordinates for {STATE_UID}"
    for c in coords:
        assert "latitude" in c
        assert "longitude" in c


@pytest.mark.asyncio
async def test_get_institution_locations_state_has_address(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    addresses = data[0]["addresses"]
    assert addresses, f"Expected at least one address for {STATE_UID}"


@pytest.mark.asyncio
async def test_get_institution_locations_address_structure(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    addr = data[0]["addresses"][0]
    assert "uid" in addr
    assert "street" in addr
    assert "city" in addr
    assert "zip_code" in addr
    assert "state_or_province" in addr
    assert "country" in addr
    assert "continent" in addr


@pytest.mark.asyncio
async def test_get_institution_locations_address_city_content(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    addr = data[0]["addresses"][0]
    assert addr["city"], "Expected city data in address"
    city_values = [e["value"] for e in addr["city"]]
    assert "Paris" in city_values


@pytest.mark.asyncio
async def test_get_institution_locations_address_country_content(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_UID})
    data = json.loads(result) if isinstance(result, str) else result
    addr = data[0]["addresses"][0]
    country_values = [e["value"] for e in addr["country"]]
    assert "France" in country_values


@pytest.mark.asyncio
async def test_get_institution_locations_root_has_coordinates(location_tool):
    result = await location_tool.ainvoke({"institution_uids": ROOT_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data[0]["coordinates"], f"Expected coordinates for {ROOT_UID}"


@pytest.mark.asyncio
async def test_get_institution_locations_root_no_address(location_tool):
    result = await location_tool.ainvoke({"institution_uids": ROOT_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert data[0]["addresses"] == [], f"Expected no address for {ROOT_UID}"


@pytest.mark.asyncio
async def test_get_institution_locations_no_location_returns_empty(location_tool):
    result = await location_tool.ainvoke({"institution_uids": STATE_NO_LOCATION_UID})
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) == 1
    assert data[0]["coordinates"] == []
    assert data[0]["addresses"] == []


@pytest.mark.asyncio
async def test_get_institution_locations_multiple_uids(location_tool):
    result = await location_tool.ainvoke({"institution_uids": f"{STATE_UID},{ROOT_UID}"})
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) == 2, f"Expected 2 entries for 2 UIDs, got {len(data)}"
    uids = {row["uid"] for row in data}
    assert STATE_UID in uids
    assert ROOT_UID in uids


@pytest.mark.asyncio
async def test_get_institution_locations_unknown_uid_returns_entry(location_tool):
    result = await location_tool.ainvoke({"institution_uids": "unknown-org-uid"})
    data = json.loads(result) if isinstance(result, str) else result
    assert len(data) == 1, "Expected one entry even for unknown UID"
    assert data[0]["uid"] == "unknown-org-uid"
    assert data[0]["coordinates"] == []
    assert data[0]["addresses"] == []
