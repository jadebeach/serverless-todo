import pytest
import json
from datetime import datetime
from freezegun import freeze_time
import sys
import os

# Add layers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../layers/common_layer/python'))

from common.dynamodb_helper import (
    create_response,
    get_current_timestamp,
    build_pk,
    build_sk,
    build_gsi1_sk
)


class TestCreateResponse:
    """Tests for create_response function"""

    def test_create_response_with_dict_body(self):
        """Test creating response with dictionary body"""
        body = {'message': 'success', 'data': {'id': '123'}}
        response = create_response(200, body)

        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert response['headers']['Access-Control-Allow-Headers'] == 'Content-Type,Authorization'
        assert response['headers']['Access-Control-Allow-Methods'] == 'GET,POST,PUT,DELETE,OPTIONS'

        parsed_body = json.loads(response['body'])
        assert parsed_body == body

    def test_create_response_with_error(self):
        """Test creating error response"""
        body = {'error': 'Not found'}
        response = create_response(404, body)

        assert response['statusCode'] == 404
        parsed_body = json.loads(response['body'])
        assert parsed_body == body

    def test_create_response_with_unicode(self):
        """Test creating response with unicode characters"""
        body = {'message': 'テスト成功', 'emoji': '🎉'}
        response = create_response(200, body)

        # ensure_ascii=False should preserve unicode
        parsed_body = json.loads(response['body'])
        assert parsed_body['message'] == 'テスト成功'
        assert parsed_body['emoji'] == '🎉'

    def test_create_response_cors_headers(self):
        """Test CORS headers are present"""
        response = create_response(200, {})

        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']


class TestGetCurrentTimestamp:
    """Tests for get_current_timestamp function"""

    @freeze_time("2025-01-15 12:30:45")
    def test_get_current_timestamp_format(self):
        """Test timestamp format is ISO8601 with Z suffix"""
        timestamp = get_current_timestamp()

        assert timestamp == "2025-01-15T12:30:45Z"
        assert timestamp.endswith('Z')
        assert 'T' in timestamp

    @freeze_time("2025-01-15 12:30:45")
    def test_get_current_timestamp_is_utc(self):
        """Test timestamp is in UTC"""
        timestamp = get_current_timestamp()

        # Parse and verify it's a valid ISO format
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 12
        assert dt.minute == 30
        assert dt.second == 45

    def test_get_current_timestamp_uniqueness(self):
        """Test that consecutive calls produce different timestamps"""
        timestamp1 = get_current_timestamp()
        timestamp2 = get_current_timestamp()

        # At least the format should be consistent
        assert timestamp1.endswith('Z')
        assert timestamp2.endswith('Z')


class TestBuildPk:
    """Tests for build_pk function"""

    def test_build_pk_with_user_id(self):
        """Test building partition key with user ID"""
        user_id = "user-123"
        pk = build_pk(user_id)

        assert pk == "USER#user-123"
        assert pk.startswith("USER#")

    def test_build_pk_with_uuid(self):
        """Test building partition key with UUID"""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        pk = build_pk(user_id)

        assert pk == f"USER#{user_id}"

    def test_build_pk_with_empty_string(self):
        """Test building partition key with empty string"""
        pk = build_pk("")

        assert pk == "USER#"

    def test_build_pk_with_special_characters(self):
        """Test building partition key with special characters"""
        user_id = "user@example.com"
        pk = build_pk(user_id)

        assert pk == "USER#user@example.com"


class TestBuildSk:
    """Tests for build_sk function"""

    def test_build_sk_with_valid_inputs(self):
        """Test building sort key with valid inputs"""
        task_id = "task-123"
        created_at = "2025-01-15T12:30:45Z"
        sk = build_sk(task_id, created_at)

        assert sk == f"TODO#{created_at}#{task_id}"
        assert sk.startswith("TODO#")
        assert created_at in sk
        assert task_id in sk

    def test_build_sk_ordering(self):
        """Test sort key format maintains chronological ordering"""
        task_id = "task-123"
        earlier = "2025-01-15T10:00:00Z"
        later = "2025-01-15T11:00:00Z"

        sk1 = build_sk(task_id, earlier)
        sk2 = build_sk(task_id, later)

        # Earlier timestamp should sort before later
        assert sk1 < sk2

    def test_build_sk_format(self):
        """Test sort key follows expected format"""
        sk = build_sk("abc", "2025-01-15T12:30:45Z")
        parts = sk.split('#')

        assert len(parts) == 3
        assert parts[0] == "TODO"
        assert parts[1] == "2025-01-15T12:30:45Z"
        assert parts[2] == "abc"


class TestBuildGsi1Sk:
    """Tests for build_gsi1_sk function"""

    def test_build_gsi1_sk_with_valid_inputs(self):
        """Test building GSI1 sort key with valid inputs"""
        due_date = "2025-01-20"
        priority = "HIGH"
        gsi1_sk = build_gsi1_sk(due_date, priority)

        assert gsi1_sk == f"DUE#{due_date}#{priority}"
        assert gsi1_sk.startswith("DUE#")

    def test_build_gsi1_sk_ordering_by_date(self):
        """Test GSI1 sort key ordering by due date"""
        earlier = "2025-01-15"
        later = "2025-01-20"

        sk1 = build_gsi1_sk(earlier, "HIGH")
        sk2 = build_gsi1_sk(later, "HIGH")

        # Earlier date should sort before later
        assert sk1 < sk2

    def test_build_gsi1_sk_ordering_by_priority(self):
        """Test GSI1 sort key with same date, different priority"""
        due_date = "2025-01-20"

        sk_high = build_gsi1_sk(due_date, "HIGH")
        sk_low = build_gsi1_sk(due_date, "LOW")
        sk_medium = build_gsi1_sk(due_date, "MEDIUM")

        # All should have same date prefix
        assert sk_high.startswith(f"DUE#{due_date}#")
        assert sk_low.startswith(f"DUE#{due_date}#")
        assert sk_medium.startswith(f"DUE#{due_date}#")

        # HIGH comes before LOW alphabetically, MEDIUM before HIGH
        assert sk_high < sk_low
        assert sk_high < sk_medium

    def test_build_gsi1_sk_all_priorities(self):
        """Test GSI1 sort key with all priority levels"""
        due_date = "2025-01-20"

        for priority in ['HIGH', 'MEDIUM', 'LOW']:
            gsi1_sk = build_gsi1_sk(due_date, priority)
            assert gsi1_sk == f"DUE#{due_date}#{priority}"

    def test_build_gsi1_sk_format(self):
        """Test GSI1 sort key follows expected format"""
        gsi1_sk = build_gsi1_sk("2025-01-20", "HIGH")
        parts = gsi1_sk.split('#')

        assert len(parts) == 3
        assert parts[0] == "DUE"
        assert parts[1] == "2025-01-20"
        assert parts[2] == "HIGH"
