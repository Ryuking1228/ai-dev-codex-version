from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app, repository


class FakeItems:
    def __init__(self):
        self.items = {}

    def list(self):
        return list(self.items.values())

    def create(self, title):
        item = {"id": str(uuid4()), "title": title}
        self.items[item["id"]] = item
        return item

    def delete(self, item_id):
        return self.items.pop(str(item_id), None) is not None


@pytest.fixture
def client():
    fake = FakeItems()
    app.dependency_overrides[repository] = lambda: fake
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_create_list_delete(client):
    response = client.post("/api/items", json={"title": "  サンプル  "})
    assert response.status_code == 201
    item = response.json()
    assert item["title"] == "サンプル"
    assert client.get("/api/items").json() == [item]
    assert client.delete(f"/api/items/{item['id']}").status_code == 204
    assert client.get("/api/items").json() == []
    assert client.delete(f"/api/items/{item['id']}").status_code == 404


@pytest.mark.parametrize("title", ["", "   ", "x" * 121])
def test_invalid_title(client, title):
    response = client.post("/api/items", json={"title": title})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"


def test_invalid_identifier(client):
    assert client.delete("/api/items/not-a-uuid").status_code == 422


def test_api_contract(client):
    spec = client.get("/openapi.json").json()
    operations = {operation["operationId"] for path in spec["paths"].values()
                  for method, operation in path.items() if method in {"get", "post", "delete"}}
    assert operations == {"health", "listItems", "createItem", "deleteItem"}


def test_problem_contract_matches_validation_response(client):
    spec = client.get("/openapi.json").json()
    error = spec["paths"]["/api/items"]["post"]["responses"]["422"]
    assert set(error["content"]) == {"application/problem+json"}
    assert client.patch('/api/items').headers['content-type'] == 'application/problem+json'
