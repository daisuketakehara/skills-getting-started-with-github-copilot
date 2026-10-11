from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

ORIGINAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    app_module.activities.clear()
    app_module.activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    yield
    app_module.activities.clear()
    app_module.activities.update(deepcopy(ORIGINAL_ACTIVITIES))


client = TestClient(app)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]


def test_signup_for_activity_success():
    email = "student@mergington.edu"

    response = client.post(f"/activities/Soccer Team/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Soccer Team"
    assert email in app_module.activities["Soccer Team"]["participants"]


def test_signup_for_activity_rejects_duplicate_and_missing_activity():
    duplicate_response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
    missing_response = client.post("/activities/Unknown Activity/signup?email=test@mergington.edu")

    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student is already signed up for this activity"
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Activity not found"


def test_delete_participant_success_and_missing_student():
    success_response = client.delete("/activities/Chess Club/participants/michael@mergington.edu")
    missing_response = client.delete("/activities/Chess Club/participants/ghost@mergington.edu")

    assert success_response.status_code == 200
    assert success_response.json()["message"] == "Removed michael@mergington.edu from Chess Club"
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Student is not signed up for this activity"


def test_delete_participant_missing_activity():
    response = client.delete("/activities/Missing Club/participants/student@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
