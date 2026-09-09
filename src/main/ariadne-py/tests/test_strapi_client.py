from __future__ import annotations

import json

import httpx

from ariadne.models import BOMEntry, Device
from ariadne.strapi_client import BOM_ENTRY_EP, DEVICE_EP, StrapiClient

DEVICE = Device(brand="STM", model_name="STEVAL-SPIN3204", manufacturer="STMicroelectronics")


def _client_with_transport(handler):
    transport = httpx.MockTransport(handler)
    client = StrapiClient.__new__(StrapiClient)
    client._base_url = "http://localhost:1337"
    client._api_token = "test"
    client._client = httpx.Client(transport=transport, base_url="http://localhost:1337", timeout=30)
    return client


def test_upsert_device_creates_when_not_found():
    log = []

    def handler(request: httpx.Request) -> httpx.Response:
        log.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"data": []})
        return httpx.Response(200, json={"data": {"id": 42}})

    client = _client_with_transport(handler)
    try:
        did = client.upsert_device(DEVICE)
    finally:
        client.close()
    assert did == 42
    # prima GET (find), poi POST (create)
    assert log[0].method == "GET"
    assert log[1].method == "POST"
    assert "/api/devices" in log[1].url.path


def test_upsert_device_updates_when_exists():
    log = []

    def handler(request: httpx.Request) -> httpx.Response:
        log.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": 7}]})
        return httpx.Response(200, json={"data": {"id": 7}})

    client = _client_with_transport(handler)
    try:
        did = client.upsert_device(DEVICE)
    finally:
        client.close()
    assert did == 7
    methods = [r.method for r in log]
    assert methods == ["GET", "PUT"]
    assert "/api/devices/7" in log[1].url.path


def test_upsert_device_uses_bearer_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization")
        if request.method == "GET":
            return httpx.Response(200, json={"data": []})
        return httpx.Response(200, json={"data": {"id": 1}})

    client = _client_with_transport(handler)
    try:
        client.upsert_device(DEVICE)
    finally:
        client.close()
    assert seen["auth"] == "Bearer test"


def test_push_bom_entry_posts_payload():
    seen = {}
    entry = BOMEntry(item_number=1, quantity=14, reference_designator="C1,C5",
                     part_value="100nF", mounting_type="SMT", eec_category_id=2)

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"id": 99}})

    client = _client_with_transport(handler)
    try:
        eid = client.push_bom_entry(DEVICE, entry, device_strapi_id=42)
    finally:
        client.close()
    assert eid == 99
    assert seen["body"]["data"]["referenceDesignator"] == "C1,C5"
    assert seen["body"]["data"]["device"] == 42
    assert seen["body"]["data"]["eecCategoryId"] == 2


def test_sync_device_pushes_device_and_entries():
    entries = [
        BOMEntry(item_number=1, quantity=1, reference_designator="R1", mounting_type="SMT"),
        BOMEntry(item_number=2, quantity=2, reference_designator="C1", mounting_type="SMT"),
    ]
    log = []

    def handler(request: httpx.Request) -> httpx.Response:
        log.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"data": []})
        if request.method == "POST" and "/api/bom-entries" in request.url.path:
            return httpx.Response(200, json={"data": {"id": 1}})
        return httpx.Response(200, json={"data": {"id": 10}})

    client = _client_with_transport(handler)
    try:
        res = client.sync_device(DEVICE, entries)
    finally:
        client.close()
    assert res == {"device_id": 10, "entries_pushed": 2}
    posts = [r for r in log if r.method == "POST"]
    bom_posts = [r for r in posts if "/api/bom-entries" in r.url.path]
    assert len(bom_posts) == 2


def test_auth_header_on_all_methods():
    headers_seen = set()

    def handler(request: httpx.Request) -> httpx.Response:
        headers_seen.add(request.headers.get("Authorization"))
        if request.method == "GET":
            return httpx.Response(200, json={"data": []})
        return httpx.Response(200, json={"data": {"id": 1}})

    client = _client_with_transport(handler)
    try:
        client.upsert_device(DEVICE)
    finally:
        client.close()
    assert headers_seen == {"Bearer test"}


def test_missing_token_no_auth_header():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"data": []})

    client = StrapiClient.__new__(StrapiClient)
    client._base_url = "http://x"
    client._api_token = ""
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://x")
    try:
        client._get(f"/api/{DEVICE_EP}", params={})
    finally:
        client.close()
    assert seen["auth"] is None
