"""Tests for analytics API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app
from datetime import datetime, UTC
import uuid

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def mock_user_dict():
    """Mock user as dictionary."""
    return {
        "id": str(uuid.uuid4()),
        "phone_number": "+15551234567",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "created_at": datetime.now(UTC).isoformat(),
        "last_call_at": datetime.now(UTC).isoformat(),
        "user_data": {"career_goal": "Software Engineer"}
    }


@pytest.fixture
def mock_conversation_dict():
    """Mock conversation as dictionary."""
    return {
        "id": str(uuid.uuid4()),
        "call_sid": "CA123456789",
        "phone_number": "+15551234567",
        "user_id": str(uuid.uuid4()),
        "started_at": datetime.now(UTC).isoformat(),
        "ended_at": None,
        "duration_seconds": None,
        "status": "active"
    }


@pytest.fixture
def mock_message_dict():
    """Mock message as dictionary."""
    return {
        "id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "role": "user",
        "content": "I need help with my resume",
        "timestamp": datetime.now(UTC).isoformat(),
        "extra_data": None
    }


class TestConversationEndpoints:
    """Test conversation-related endpoints."""
    
    def test_get_all_conversations(self, mock_db, mock_conversation_dict):
        """Test getting all conversations."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_all_conversations', return_value=[mock_conversation_dict]):
                response = client.get("/analytics/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "count" in data
        assert data["count"] == 1
    
    def test_get_conversations_pagination(self, mock_db, mock_conversation_dict):
        """Test conversation pagination."""
        conversations = [mock_conversation_dict for _ in range(5)]
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_all_conversations', return_value=conversations):
                response = client.get("/analytics/conversations?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 2
    
    def test_get_conversation_by_id(self, mock_db, mock_conversation_dict):
        """Test getting conversation by ID."""
        conv_id = mock_conversation_dict["id"]
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversation_by_id', return_value=mock_conversation_dict):
                response = client.get(f"/analytics/conversations/{conv_id}")
        
        assert response.status_code == 200
    
    def test_get_conversation_by_id_not_found(self, mock_db):
        """Test getting non-existent conversation."""
        conv_id = str(uuid.uuid4())
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversation_by_id', return_value=None):
                response = client.get(f"/analytics/conversations/{conv_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_conversation_by_id_invalid_uuid(self, mock_db):
        """Test getting conversation with invalid UUID."""
        response = client.get("/analytics/conversations/invalid-uuid")
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_conversation_by_call_sid(self, mock_db, mock_conversation_dict):
        """Test getting conversation by call SID."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversation_by_call_sid', return_value=mock_conversation_dict):
                response = client.get(f"/analytics/conversations/call/{mock_conversation_dict['call_sid']}")
        
        assert response.status_code == 200
    
    def test_get_conversation_by_call_sid_not_found(self, mock_db):
        """Test getting conversation by non-existent call SID."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversation_by_call_sid', return_value=None):
                response = client.get("/analytics/conversations/call/CA999999")
        
        assert response.status_code == 404
    
    def test_get_conversation_messages(self, mock_db, mock_message_dict):
        """Test getting messages for a conversation."""
        conv_id = str(uuid.uuid4())
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversation_messages', return_value=[mock_message_dict]):
                response = client.get(f"/analytics/conversations/{conv_id}/messages")
        
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "count" in data
        assert data["count"] == 1
    
    def test_get_conversation_messages_invalid_uuid(self, mock_db):
        """Test getting messages with invalid conversation ID."""
        response = client.get("/analytics/conversations/invalid-uuid/messages")
        
        assert response.status_code == 400


class TestUserEndpoints:
    """Test user-related endpoints."""
    
    def test_get_all_users(self, mock_db, mock_user_dict):
        """Test getting all users."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_all_users', return_value=[mock_user_dict]):
                response = client.get("/analytics/users")
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "count" in data
        assert data["count"] == 1
    
    def test_get_all_users_pagination(self, mock_db, mock_user_dict):
        """Test user pagination."""
        users = [mock_user_dict for _ in range(5)]
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_all_users', return_value=users):
                response = client.get("/analytics/users?skip=0&limit=3")
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 3
    
    def test_get_user_by_phone(self, mock_db, mock_user_dict):
        """Test getting user by phone number."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_user_by_phone', return_value=mock_user_dict):
                response = client.get(f"/analytics/users/{mock_user_dict['phone_number']}")
        
        assert response.status_code == 200
    
    def test_get_user_by_phone_not_found(self, mock_db):
        """Test getting non-existent user."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_user_by_phone', return_value=None):
                response = client.get("/analytics/users/+15559999999")
        
        assert response.status_code == 404
    
    def test_get_user_invalid_phone_format(self, mock_db):
        """Test getting user with invalid phone format (no +)."""
        response = client.get("/analytics/users/15551234567")
        
        assert response.status_code == 400
        assert "must start with +" in response.json()["detail"]
    
    def test_get_user_conversations(self, mock_db, mock_conversation_dict):
        """Test getting user's conversations."""
        phone = "+15551234567"
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversations_by_phone', return_value=[mock_conversation_dict]):
                response = client.get(f"/analytics/users/{phone}/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert "phone_number" in data
        assert "conversations" in data
        assert data["phone_number"] == phone
    
    def test_get_user_conversations_empty(self, mock_db):
        """Test getting conversations for user with no conversations."""
        phone = "+15559999999"
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversations_by_phone', return_value=[]):
                response = client.get(f"/analytics/users/{phone}/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
    
    def test_get_user_conversations_pagination(self, mock_db, mock_conversation_dict):
        """Test pagination of user conversations."""
        phone = "+15551234567"
        conversations = [mock_conversation_dict for _ in range(5)]
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_conversations_by_phone', return_value=conversations):
                response = client.get(f"/analytics/users/{phone}/conversations?skip=1&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 1
        assert data["limit"] == 2
        assert data["total_count"] == 5


class TestStatsEndpoint:
    """Test statistics endpoint."""
    
    def test_get_stats(self, mock_db):
        """Test getting analytics statistics."""
        mock_stats = {
            "total_users": 10,
            "total_conversations": 25,
            "active_conversations": 3,
            "completed_conversations": 22,
            "total_messages": 150,
            "average_messages_per_conversation": 6.0,
            "average_duration_seconds": 180.5
        }
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_stats', return_value=mock_stats):
                response = client.get("/analytics/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 10
        assert data["total_conversations"] == 25
        assert data["active_conversations"] == 3
        assert data["average_duration_seconds"] == 180.5
    
    def test_get_stats_empty_database(self, mock_db):
        """Test stats with empty database."""
        mock_stats = {
            "total_users": 0,
            "total_conversations": 0,
            "active_conversations": 0,
            "completed_conversations": 0,
            "total_messages": 0,
            "average_messages_per_conversation": 0,
            "average_duration_seconds": 0
        }
        
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_stats', return_value=mock_stats):
                response = client.get("/analytics/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 0


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_database_error_on_conversations(self, mock_db):
        """Test database error handling."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_all_conversations', side_effect=Exception("DB Error")):
                response = client.get("/analytics/conversations")
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
    
    def test_database_error_on_users(self, mock_db):
        """Test database error on user endpoint."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_all_users', side_effect=Exception("DB Error")):
                response = client.get("/analytics/users")
        
        assert response.status_code == 500
    
    def test_database_error_on_stats(self, mock_db):
        """Test database error on stats endpoint."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_stats', side_effect=Exception("DB Error")):
                response = client.get("/analytics/stats")
        
        assert response.status_code == 500


class TestQueryParameters:
    """Test query parameter validation."""
    
    def test_negative_skip(self, mock_db):
        """Test negative skip parameter."""
        response = client.get("/analytics/conversations?skip=-1")
        
        assert response.status_code == 422  # Validation error
    
    def test_zero_limit(self, mock_db):
        """Test zero limit parameter."""
        response = client.get("/analytics/conversations?limit=0")
        
        assert response.status_code == 422
    
    def test_excessive_limit(self, mock_db):
        """Test excessive limit parameter."""
        response = client.get("/analytics/conversations?limit=1000")
        
        assert response.status_code == 422
    
    def test_valid_pagination_params(self, mock_db, mock_conversation_dict):
        """Test valid pagination parameters."""
        with patch('src.api.routes.analytics.get_db', return_value=iter([mock_db])):
            with patch('src.api.routes.analytics.analytics_service.get_all_conversations', return_value=[mock_conversation_dict]):
                response = client.get("/analytics/conversations?skip=10&limit=50")
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 50