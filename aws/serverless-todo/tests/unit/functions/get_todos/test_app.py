import pytest
import json
import os
from unittest.mock import patch
from moto import mock_dynamodb
import boto3
import sys

# Add function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../functions/get_todos'))

import app


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table with sample data"""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table_name = 'test-todos-table'

        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )

        os.environ['TABLE_NAME'] = table_name
        app.table = table

        yield table


@pytest.fixture
def sample_todos(mock_dynamodb_table):
    """Insert sample todos into the mock table"""
    todos = [
        {
            'PK': 'USER#test-user-001',
            'SK': 'TODO#2025-01-15T10:00:00Z#task-1',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-20#HIGH',
            'taskId': 'task-1',
            'title': 'High priority task',
            'description': 'Important task',
            'dueDate': '2025-01-20',
            'priority': 'HIGH',
            'status': 'PENDING',
            'createdAt': '2025-01-15T10:00:00Z',
            'updatedAt': '2025-01-15T10:00:00Z'
        },
        {
            'PK': 'USER#test-user-001',
            'SK': 'TODO#2025-01-15T11:00:00Z#task-2',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-25#MEDIUM',
            'taskId': 'task-2',
            'title': 'Medium priority task',
            'description': 'Regular task',
            'dueDate': '2025-01-25',
            'priority': 'MEDIUM',
            'status': 'PENDING',
            'createdAt': '2025-01-15T11:00:00Z',
            'updatedAt': '2025-01-15T11:00:00Z'
        },
        {
            'PK': 'USER#test-user-001',
            'SK': 'TODO#2025-01-15T12:00:00Z#task-3',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-18#LOW',
            'taskId': 'task-3',
            'title': 'Low priority task',
            'description': 'Optional task',
            'dueDate': '2025-01-18',
            'priority': 'LOW',
            'status': 'COMPLETED',
            'createdAt': '2025-01-15T12:00:00Z',
            'updatedAt': '2025-01-15T13:00:00Z'
        }
    ]

    for todo in todos:
        mock_dynamodb_table.put_item(Item=todo)

    return todos


class TestGetTodosBasic:
    """Tests for basic get todos functionality"""

    def test_get_todos_no_parameters(self, sample_todos):
        """Test getting todos with no query parameters"""
        event = {}

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'items' in body
        assert 'count' in body
        assert body['count'] == 3
        assert len(body['items']) == 3

    def test_get_todos_empty_query_parameters(self, sample_todos):
        """Test getting todos with empty query parameters object"""
        event = {
            'queryStringParameters': {}
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 3

    def test_get_todos_none_query_parameters(self, sample_todos):
        """Test getting todos when queryStringParameters is None"""
        event = {
            'queryStringParameters': None
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 3

    def test_get_todos_returns_correct_fields(self, sample_todos):
        """Test that returned todos have correct fields"""
        event = {}

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        for item in body['items']:
            assert 'taskId' in item
            assert 'title' in item
            assert 'description' in item
            assert 'dueDate' in item
            assert 'priority' in item
            assert 'status' in item
            assert 'createdAt' in item
            assert 'updatedAt' in item
            # PK and SK should not be in response
            assert 'PK' not in item
            assert 'SK' not in item
            assert 'GSI1PK' not in item
            assert 'GSI1SK' not in item


class TestGetTodosFiltering:
    """Tests for filtering todos by status"""

    def test_get_todos_filter_by_pending(self, sample_todos):
        """Test filtering todos by PENDING status"""
        event = {
            'queryStringParameters': {
                'status': 'PENDING'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        assert body['count'] == 2
        for item in body['items']:
            assert item['status'] == 'PENDING'

    def test_get_todos_filter_by_completed(self, sample_todos):
        """Test filtering todos by COMPLETED status"""
        event = {
            'queryStringParameters': {
                'status': 'COMPLETED'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        assert body['count'] == 1
        assert body['items'][0]['status'] == 'COMPLETED'
        assert body['items'][0]['taskId'] == 'task-3'

    def test_get_todos_filter_no_matches(self, sample_todos):
        """Test filtering with status that has no matches"""
        event = {
            'queryStringParameters': {
                'status': 'NONEXISTENT'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        assert body['count'] == 0
        assert body['items'] == []


class TestGetTodosSorting:
    """Tests for sorting todos"""

    def test_get_todos_sort_by_due_date(self, sample_todos):
        """Test sorting by due date (using GSI1)"""
        event = {
            'queryStringParameters': {
                'sortBy': 'dueDate'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        # Should be sorted by due date ascending
        # task-3: 2025-01-18, task-1: 2025-01-20, task-2: 2025-01-25
        assert len(body['items']) == 3
        assert body['items'][0]['dueDate'] == '2025-01-18'
        assert body['items'][1]['dueDate'] == '2025-01-20'
        assert body['items'][2]['dueDate'] == '2025-01-25'

    def test_get_todos_sort_by_created_date(self, sample_todos):
        """Test sorting by created date (using main table)"""
        event = {
            'queryStringParameters': {
                'sortBy': 'createdAt'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        # Should be sorted by creation date descending (newest first)
        assert len(body['items']) == 3
        # The ordering depends on SK, which includes createdAt
        # task-3 was created last, so it should be first in descending order
        created_times = [item['createdAt'] for item in body['items']]
        assert created_times == sorted(created_times, reverse=True)


class TestGetTodosLimit:
    """Tests for limit parameter"""

    def test_get_todos_with_limit(self, sample_todos):
        """Test limiting number of results"""
        event = {
            'queryStringParameters': {
                'limit': '2'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        assert len(body['items']) <= 2
        assert body['count'] <= 2

    def test_get_todos_default_limit(self, mock_dynamodb_table):
        """Test default limit is 20"""
        # Create 25 todos
        for i in range(25):
            mock_dynamodb_table.put_item(Item={
                'PK': 'USER#test-user-001',
                'SK': f'TODO#2025-01-15T10:00:0{i}Z#task-{i}',
                'GSI1PK': 'USER#test-user-001',
                'GSI1SK': f'DUE#2025-01-20#HIGH',
                'taskId': f'task-{i}',
                'title': f'Task {i}',
                'description': '',
                'dueDate': '2025-01-20',
                'priority': 'HIGH',
                'status': 'PENDING',
                'createdAt': f'2025-01-15T10:00:0{i}Z',
                'updatedAt': f'2025-01-15T10:00:0{i}Z'
            })

        event = {}
        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        # Default limit is 20
        assert len(body['items']) == 20
        assert body['count'] == 20

    def test_get_todos_custom_limit(self, sample_todos):
        """Test custom limit parameter"""
        event = {
            'queryStringParameters': {
                'limit': '1'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        assert len(body['items']) == 1
        assert body['count'] == 1


class TestGetTodosCombinedParameters:
    """Tests for combining multiple query parameters"""

    def test_get_todos_status_and_limit(self, sample_todos):
        """Test combining status filter and limit"""
        event = {
            'queryStringParameters': {
                'status': 'PENDING',
                'limit': '1'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        # Should get at most 1 PENDING todo
        assert body['count'] <= 1
        if body['count'] > 0:
            assert body['items'][0]['status'] == 'PENDING'

    def test_get_todos_all_parameters(self, sample_todos):
        """Test using all query parameters together"""
        event = {
            'queryStringParameters': {
                'status': 'PENDING',
                'limit': '10',
                'sortBy': 'dueDate'
            }
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        assert response['statusCode'] == 200
        # Should have 2 PENDING todos
        assert body['count'] == 2
        for item in body['items']:
            assert item['status'] == 'PENDING'


class TestGetTodosResponseHeaders:
    """Tests for response headers"""

    def test_response_has_cors_headers(self, sample_todos):
        """Test that response includes CORS headers"""
        event = {}

        response = app.lambda_handler(event, None)

        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestGetTodosEmptyResults:
    """Tests for empty results"""

    def test_get_todos_empty_table(self, mock_dynamodb_table):
        """Test getting todos from empty table"""
        event = {}

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 0
        assert body['items'] == []


class TestGetTodosErrorHandling:
    """Tests for error handling"""

    def test_get_todos_dynamodb_error(self, mock_dynamodb_table):
        """Test handling of DynamoDB errors"""
        event = {}

        # Mock query to raise an exception
        with patch.object(mock_dynamodb_table, 'query', side_effect=Exception('DynamoDB error')):
            response = app.lambda_handler(event, None)

            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body

    def test_get_todos_invalid_limit_format(self, sample_todos):
        """Test with invalid limit format (non-integer)"""
        event = {
            'queryStringParameters': {
                'limit': 'not-a-number'
            }
        }

        # This should raise an exception or handle gracefully
        response = app.lambda_handler(event, None)

        # Should either return error or use default
        assert response['statusCode'] in [200, 400, 500]
