from fastapi.testclient import TestClient

from app.main import app


def test_health_and_job_submission_flow() -> None:
    client = TestClient(app)

    live = client.get("/health/live")
    assert live.status_code == 200

    response = client.post(
        "/jobs/search",
        json={
            "raw_request": "machine learning hcmus pdf",
            "goal": "exam_preparation",
            "preferred_formats": ["pdf"],
            "max_downloads": 2,
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["job_id"].startswith("job_")

    status_response = client.get(f"/jobs/{payload['job_id']}")
    assert status_response.status_code == 200
