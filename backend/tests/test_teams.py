import uuid

from fastapi.testclient import TestClient


class TestTeamsAPI:
    def test_list_teams_empty(self, client: TestClient):
        resp = client.get("/api/v1/teams")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_team(self, client: TestClient):
        data = {"name": "Brazil", "fifa_code": "BRA", "continent": "South America"}
        resp = client.post("/api/v1/teams", json=data)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Brazil"
        assert body["fifa_code"] == "BRA"
        assert "id" in body

    def test_get_team_not_found(self, client: TestClient):
        resp = client.get(f"/api/v1/teams/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_get_team_by_id(self, client: TestClient):
        create_resp = client.post("/api/v1/teams", json={"name": "Argentina", "fifa_code": "ARG"})
        team_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/teams/{team_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Argentina"
