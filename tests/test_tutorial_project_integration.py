import os
import sys
from pathlib import Path

import pytest

# Add the tutorial project to the Python path
tutorial_path = Path(__file__).parent / "tutorial_project"
sys.path.insert(0, str(tutorial_path))


import django
from django.test import Client
from django.utils import timezone

# Set up Django settings for the tutorial project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tutorial_project.settings")
django.setup()

from polls.models import Choice, Question


@pytest.mark.django_db
class TestTutorialProjectIntegration:
    """Test the Django Debug Toolbar with the official tutorial project."""

    def setup_method(self):
        """Set up the test client."""
        self.client = Client()

    def test_part1_models(self):
        """Test Part 1: Models - Creating questions and choices."""
        # Create a question with timezone-aware datetime
        question = Question.objects.create(
            question_text="What's new?", pub_date=timezone.now()
        )
        assert str(question) == "What's new?"

        # Create choices
        choice1 = Choice.objects.create(
            question=question, choice_text="Not much", votes=0
        )
        choice2 = Choice.objects.create(
            question=question, choice_text="Just coding", votes=0
        )

        assert question.choice_set.count() == 2
        assert str(choice1) == "Not much"
        assert str(choice2) == "Just coding"

    def test_part2_admin_access(self):
        """Test Part 2: Admin - Admin interface loads."""
        response = self.client.get("/admin/")
        assert response.status_code == 302  # Redirects to login

    def test_part3_views_with_toolbar(self):
        """Test Part 3: Views - Index and detail views with toolbar."""
        # Create test data with timezone-aware datetime
        question = Question.objects.create(
            question_text="Test question", pub_date=timezone.now()
        )
        Choice.objects.create(question=question, choice_text="Option A", votes=0)

        # Test index view
        response = self.client.get("/polls/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test question" in content
        assert "djdt" in content  # Debug toolbar should be present

        # Test detail view
        response = self.client.get(f"/polls/{question.id}/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Option A" in content
        assert "djdt" in content

    def test_part4_forms_and_voting(self):
        """Test Part 4: Forms - Voting functionality with toolbar."""
        # Create question with choices
        question = Question.objects.create(
            question_text="Vote test", pub_date=timezone.now()
        )
        choice = Choice.objects.create(
            question=question, choice_text="Option 1", votes=0
        )

        # Test voting
        response = self.client.post(
            f"/polls/{question.id}/vote/", {"choice": choice.id}
        )
        assert response.status_code == 200
        content = response.content.decode()

        # Check vote was counted
        choice.refresh_from_db()
        assert choice.votes == 1
        assert "Option 1 -- 1 vote" in content
        assert "djdt" in content

        # Test results view
        response = self.client.get(f"/polls/{question.id}/results/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Option 1" in content
        assert "1 vote" in content
        assert "djdt" in content

    def test_invalid_vote_handling(self):
        """Test error handling when voting without selecting a choice."""
        question = Question.objects.create(
            question_text="Invalid vote test", pub_date=timezone.now()
        )
        Choice.objects.create(question=question, choice_text="Only choice", votes=0)

        # Post without selecting a choice
        response = self.client.post(
            f"/polls/{question.id}/vote/",
            {},  # No choice selected
        )
        assert response.status_code == 200
        content = response.content.decode()

        # Check for the error message (with HTML escaping)
        assert "You didn&#x27;t select a choice." in content
        assert "djdt" in content
