"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state after each test"""
    # Store initial state
    initial_state = {
        k: {"participants": v["participants"].copy(), **{k2: v2 for k2, v2 in v.items() if k2 != "participants"}}
        for k, v in activities.items()
    }
    yield
    # Restore initial state
    for activity_name, activity_data in initial_state.items():
        activities[activity_name]["participants"] = activity_data["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that all expected activities are returned"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Basketball Club",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Math Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing field {field}"

    def test_activity_participants_is_list(self, client):
        """Test that participants is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up newstudent@mergington.edu for Basketball Club" in response.json()["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Basketball%20Club/signup?email={email}")
        
        response = client.get("/activities")
        participants = response.json()["Basketball Club"]["participants"]
        assert email in participants

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """Test that signing up twice returns a 400 error"""
        email = "alex@mergington.edu"  # Already signed up for Basketball Club
        response = client.post(
            f"/activities/Basketball%20Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        email = "newstudent@mergington.edu"
        
        # Sign up for Basketball Club
        response1 = client.post(
            f"/activities/Basketball%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Tennis Club
        response2 = client.post(
            f"/activities/Tennis%20Club/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups were successful
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Club"]["participants"]
        assert email in data["Tennis Club"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        email = "alex@mergington.edu"  # Already in Basketball Club
        response = client.post(
            f"/activities/Basketball%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert f"{email} has been unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "alex@mergington.edu"
        client.post(f"/activities/Basketball%20Club/unregister?email={email}")
        
        response = client.get("/activities")
        participants = response.json()["Basketball Club"]["participants"]
        assert email not in participants

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_participant_returns_400(self, client):
        """Test that unregistering a non-existent participant returns 400"""
        response = client.post(
            "/activities/Basketball%20Club/unregister?email=notarealstudent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
