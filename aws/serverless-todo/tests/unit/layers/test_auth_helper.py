import pytest
import sys
import os

# Add layers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../layers/common_layer/python'))

from common.auth_helper import get_user_id_from_event


class TestGetUserIdFromEvent:
    """Tests for get_user_id_from_event function"""

    def test_get_user_id_with_valid_cognito_claims(self):
        """Test extracting user ID from valid Cognito claims"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123-456-789',
                        'email': 'test@example.com',
                        'cognito:username': 'testuser'
                    }
                }
            }
        }

        user_id = get_user_id_from_event(event)
        assert user_id == 'user-123-456-789'

    def test_get_user_id_with_uuid_sub(self):
        """Test extracting UUID format user ID"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': '550e8400-e29b-41d4-a716-446655440000'
                    }
                }
            }
        }

        user_id = get_user_id_from_event(event)
        assert user_id == '550e8400-e29b-41d4-a716-446655440000'

    def test_get_user_id_missing_request_context(self):
        """Test error when requestContext is missing"""
        event = {}

        with pytest.raises(ValueError) as exc_info:
            get_user_id_from_event(event)

        assert 'User ID not found' in str(exc_info.value)

    def test_get_user_id_missing_authorizer(self):
        """Test error when authorizer is missing"""
        event = {
            'requestContext': {}
        }

        with pytest.raises(ValueError) as exc_info:
            get_user_id_from_event(event)

        assert 'User ID not found' in str(exc_info.value)

    def test_get_user_id_missing_claims(self):
        """Test error when claims are missing"""
        event = {
            'requestContext': {
                'authorizer': {}
            }
        }

        with pytest.raises(ValueError) as exc_info:
            get_user_id_from_event(event)

        assert 'User ID not found' in str(exc_info.value)

    def test_get_user_id_missing_sub_claim(self):
        """Test error when sub claim is missing"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'email': 'test@example.com',
                        'cognito:username': 'testuser'
                    }
                }
            }
        }

        with pytest.raises(ValueError) as exc_info:
            get_user_id_from_event(event)

        assert 'User ID not found' in str(exc_info.value)

    def test_get_user_id_empty_sub_claim(self):
        """Test error when sub claim is empty string"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': ''
                    }
                }
            }
        }

        with pytest.raises(ValueError) as exc_info:
            get_user_id_from_event(event)

        assert 'User ID not found' in str(exc_info.value)

    def test_get_user_id_none_sub_claim(self):
        """Test error when sub claim is None"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': None
                    }
                }
            }
        }

        with pytest.raises(ValueError) as exc_info:
            get_user_id_from_event(event)

        assert 'User ID not found' in str(exc_info.value)

    def test_get_user_id_with_additional_claims(self):
        """Test that only sub claim is returned, not other claims"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-abc-123',
                        'email': 'test@example.com',
                        'cognito:username': 'testuser',
                        'custom:role': 'admin'
                    }
                }
            }
        }

        user_id = get_user_id_from_event(event)
        assert user_id == 'user-abc-123'
        assert user_id != 'test@example.com'
        assert user_id != 'testuser'

    def test_get_user_id_error_message_format(self):
        """Test that error message contains helpful information"""
        event = {'invalid': 'structure'}

        with pytest.raises(ValueError) as exc_info:
            get_user_id_from_event(event)

        error_message = str(exc_info.value)
        assert 'User ID not found' in error_message or 'Failed to get user ID' in error_message
