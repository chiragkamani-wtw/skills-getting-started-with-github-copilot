"""
Unit tests for the FastAPI activity management application.
Tests follow the Arrange-Act-Assert (AAA) pattern.
"""

import pytest


class TestRootEndpoint:
    """Tests for the GET / endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """
        Test that GET / redirects to /static/index.html
        
        Arrange: Test client is ready
        Act: Make GET request to /
        Assert: Verify redirect (307) with correct Location header
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Test that GET /activities returns all activities with correct structure
        
        Arrange: Test client with 9 activities populated
        Act: Make GET request to /activities
        Assert: Verify 200 status and all 9 activities returned with correct fields
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_contains_required_fields(self, client):
        """
        Test that each activity has all required fields
        
        Arrange: Test client with populated activities
        Act: Make GET request to /activities
        Assert: Verify each activity has description, schedule, max_participants, participants
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)
    
    def test_get_activities_returns_correct_participant_count(self, client):
        """
        Test that activities return correct participant data
        
        Arrange: Test client with known participant data
        Act: Make GET request to /activities
        Assert: Verify specific activity has expected participants
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success_adds_participant(self, client):
        """
        Test successful signup adds new participant to activity
        
        Arrange: Create client, select activity with available spots, new email
        Act: POST to /activities/Chess Club/signup?email=newstudent@mergington.edu
        Assert: Verify 200 status, confirmation message, participant added to list
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert new_email in response.json()["message"]
        
        # Verify participant was actually added
        activities_response = client.get("/activities")
        updated_activity = activities_response.json()[activity_name]
        assert new_email in updated_activity["participants"]
    
    def test_signup_activity_not_found_returns_404(self, client):
        """
        Test signup for non-existent activity returns 404 error
        
        Arrange: Create client with non-existent activity name
        Act: POST to /activities/Nonexistent Activity/signup
        Assert: Verify 404 status code and error message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_email_returns_400(self, client):
        """
        Test that duplicate signup for same activity returns 400 error
        
        Arrange: Create client, use existing participant email
        Act: POST to /activities/Chess Club/signup with already-registered email
        Assert: Verify 400 status code and duplicate signup error message
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_multiple_different_activities_allowed(self, client):
        """
        Test that same student can signup for multiple different activities
        
        Arrange: Create client and student email
        Act: POST signup to two different activities with same email
        Assert: Verify both signups succeed (200 status both times)
        """
        # Arrange
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Chess Club", "Drama Club"]
        
        # Act & Assert
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint."""
    
    def test_unregister_success_removes_participant(self, client):
        """
        Test successful unregister removes participant from activity
        
        Arrange: Create client, select activity with known participant
        Act: DELETE /activities/Chess Club/participants?email=michael@mergington.edu
        Assert: Verify 200 status, confirmation message, participant removed from list
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        
        # Verify participant exists before removal
        activities_response = client.get("/activities")
        activity = activities_response.json()[activity_name]
        initial_count = len(activity["participants"])
        assert email_to_remove in activity["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify participant was actually removed
        activities_response = client.get("/activities")
        updated_activity = activities_response.json()[activity_name]
        assert email_to_remove not in updated_activity["participants"]
        assert len(updated_activity["participants"]) == initial_count - 1
    
    def test_unregister_activity_not_found_returns_404(self, client):
        """
        Test unregister from non-existent activity returns 404 error
        
        Arrange: Create client with non-existent activity name
        Act: DELETE /activities/Nonexistent Activity/participants
        Assert: Verify 404 status code and error message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_student_not_in_activity_returns_404(self, client):
        """
        Test unregister for participant not in activity returns 404 error
        
        Arrange: Create client, use email not in Chess Club
        Act: DELETE /activities/Chess Club/participants with non-participant email
        Assert: Verify 404 status code and not signed up error message
        """
        # Arrange
        activity_name = "Chess Club"
        email_not_in_activity = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email_not_in_activity}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_multiple_participants_from_same_activity(self, client):
        """
        Test removing multiple different participants from same activity
        
        Arrange: Create client, select activity with multiple participants
        Act: DELETE two different participants sequentially
        Assert: Verify both removals succeed and participant count decreases each time
        """
        # Arrange
        activity_name = "Chess Club"
        emails_to_remove = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act & Assert
        for email in emails_to_remove:
            response = client.delete(
                f"/activities/{activity_name}/participants",
                params={"email": email}
            )
            assert response.status_code == 200
            
            # Verify removal
            activities_response = client.get("/activities")
            updated_activity = activities_response.json()[activity_name]
            assert email not in updated_activity["participants"]


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""
    
    def test_signup_then_unregister_workflow(self, client):
        """
        Test complete workflow: signup to activity, then unregister
        
        Arrange: Create client with known activity
        Act: 1) POST signup, 2) GET activities, 3) DELETE unregister, 4) GET activities
        Assert: Verify signup successful, unregister successful, final state correct
        """
        # Arrange
        activity_name = "Programming Class"
        email = "workflow@mergington.edu"
        
        # Act: Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act: Verify signup by getting activities
        get_response_after_signup = client.get("/activities")
        activity_after_signup = get_response_after_signup.json()[activity_name]
        assert email in activity_after_signup["participants"]
        initial_count_after_signup = len(activity_after_signup["participants"])
        
        # Act: Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Assert: Verify unregister by getting activities
        get_response_after_unregister = client.get("/activities")
        activity_after_unregister = get_response_after_unregister.json()[activity_name]
        assert email not in activity_after_unregister["participants"]
        assert len(activity_after_unregister["participants"]) == initial_count_after_signup - 1
    
    def test_multiple_signups_independent_state(self, client):
        """
        Test that signups are independent per activity
        
        Arrange: Create client with two activities and one student
        Act: 1) Signup to Chess Club, 2) Signup to Drama Club
        Assert: Verify both signups succeed and activities have correct participant lists
        """
        # Arrange
        email = "multiactivity@mergington.edu"
        
        # Act: Signup to Chess Club
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Act: Signup to Drama Club
        response2 = client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Assert: Verify both activities contain the participant
        get_response = client.get("/activities")
        activities_data = get_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Drama Club"]["participants"]
