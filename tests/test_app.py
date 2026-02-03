"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state after each test"""
    initial_state = {
        "Basketball": {
            "description": "Team basketball practice and intramural games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": []
        },
        "Tennis Club": {
            "description": "Tennis lessons and match competitions",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": []
        },
        "Drama Club": {
            "description": "Theater performances and acting workshops",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": []
        },
        "Visual Arts": {
            "description": "Painting, drawing, and sculpture techniques",
            "schedule": "Saturdays, 10:00 AM - 12:00 PM",
            "max_participants": 18,
            "participants": []
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking skills",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 16,
            "participants": []
        },
        "Robotics Club": {
            "description": "Build and program robots for competitions",
            "schedule": "Thursdays and Saturdays, 3:30 PM - 5:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    yield
    # Reset activities after test
    activities.clear()
    activities.update(initial_state)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all activities are present
        assert "Basketball" in data
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify activity structure
        assert "description" in data["Basketball"]
        assert "schedule" in data["Basketball"]
        assert "max_participants" in data["Basketball"]
        assert "participants" in data["Basketball"]

    def test_activities_have_correct_participants(self, client, reset_activities):
        """Test that activities have the correct initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Check pre-populated participants
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        assert len(data["Basketball"]["participants"]) == 0


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity(self, client, reset_activities):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "alice@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signup increases participant count"""
        client.post("/activities/Basketball/signup?email=alice@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "alice@mergington.edu" in data["Basketball"]["participants"]
        assert len(data["Basketball"]["participants"]) == 1

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that duplicate signups are rejected"""
        client.post("/activities/Basketball/signup?email=alice@mergington.edu")
        
        # Try to sign up again
        response = client.post(
            "/activities/Basketball/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/NonExistent/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_full_activity(self, client, reset_activities):
        """Test signup for a full activity"""
        # Fill up the Chess Club (max 12 participants, currently has 2)
        for i in range(10):
            client.post(f"/activities/Chess Club/signup?email=student{i}@mergington.edu")
        
        # Try to add one more (should fail)
        response = client.post(
            "/activities/Chess Club/signup?email=extra@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_from_activity(self, client, reset_activities):
        """Test unregistering from an activity"""
        # First sign up
        client.post("/activities/Basketball/signup?email=alice@mergington.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Basketball/unregister?email=alice@mergington.edu"
        )
        assert response.status_code == 200
        assert "alice@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes the participant"""
        client.post("/activities/Basketball/signup?email=alice@mergington.edu")
        client.delete("/activities/Basketball/unregister?email=alice@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "alice@mergington.edu" not in data["Basketball"]["participants"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister for activity that doesn't exist"""
        response = client.delete(
            "/activities/NonExistent/unregister?email=alice@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_student_not_signed_up(self, client, reset_activities):
        """Test unregister for student not signed up"""
        response = client.delete(
            "/activities/Basketball/unregister?email=alice@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify they're removed
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]


class TestRoot:
    """Tests for GET / endpoint"""

    def test_root_redirects(self, client):
        """Test that root redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
