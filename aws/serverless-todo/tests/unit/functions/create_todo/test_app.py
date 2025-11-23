import pytest
import json
import os
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb
import boto3
from freezegun import freeze_time
import sys

# Add function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../functions/create_todo'))

import app


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table for testing"""
    with mock_dynamodb():
        # Create mock table
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

        # Set environment variable
        os.environ['TABLE_NAME'] = table_name

        # Patch the app's table reference
        app.table = table

        yield table


class TestCreateTodoValidation:
    """Tests for input validation"""

    def test_missing_title(self, mock_dynamodb_table):
        """Test error when title is missing"""
        event = {
            'body': json.dumps({
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'title' in body['error'].lower()

    def test_empty_title(self, mock_dynamodb_table):
        """Test error when title is empty string"""
        event = {
            'body': json.dumps({
                'title': '',
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'title' in body['error'].lower()

    def test_missing_due_date(self, mock_dynamodb_table):
        """Test error when dueDate is missing"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'dueDate' in body['error']

    def test_empty_due_date(self, mock_dynamodb_table):
        """Test error when dueDate is empty"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'dueDate' in body['error']

    def test_missing_priority(self, mock_dynamodb_table):
        """Test error when priority is missing"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'priority' in body['error']

    def test_empty_priority(self, mock_dynamodb_table):
        """Test error when priority is empty"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20',
                'priority': ''
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'priority' in body['error']

    def test_invalid_priority_value(self, mock_dynamodb_table):
        """Test error when priority is not HIGH, MEDIUM, or LOW"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20',
                'priority': 'URGENT'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'HIGH, MEDIUM, or LOW' in body['error']

    def test_invalid_json(self, mock_dynamodb_table):
        """Test error when request body is invalid JSON"""
        event = {
            'body': 'not valid json {'
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'JSON' in body['error']


class TestCreateTodoSuccess:
    """Tests for successful todo creation"""

    @freeze_time("2025-01-15 12:30:45")
    def test_create_todo_with_all_fields(self, mock_dynamodb_table):
        """Test creating todo with all fields"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'description': 'This is a test task',
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'message' in body
        assert 'todo' in body
        assert body['todo']['title'] == 'Test Task'
        assert body['todo']['description'] == 'This is a test task'
        assert body['todo']['dueDate'] == '2025-01-20'
        assert body['todo']['priority'] == 'HIGH'
        assert body['todo']['status'] == 'PENDING'
        assert 'taskId' in body['todo']
        assert body['todo']['createdAt'] == '2025-01-15T12:30:45Z'
        assert body['todo']['updatedAt'] == '2025-01-15T12:30:45Z'

    @freeze_time("2025-01-15 12:30:45")
    def test_create_todo_without_description(self, mock_dynamodb_table):
        """Test creating todo without optional description"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20',
                'priority': 'MEDIUM'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['todo']['title'] == 'Test Task'
        assert body['todo']['description'] == ''
        assert body['todo']['priority'] == 'MEDIUM'

    @freeze_time("2025-01-15 12:30:45")
    @pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
    def test_create_todo_with_all_priority_levels(self, mock_dynamodb_table, priority):
        """Test creating todo with each priority level"""
        event = {
            'body': json.dumps({
                'title': f'Task with {priority} priority',
                'dueDate': '2025-01-20',
                'priority': priority
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['todo']['priority'] == priority

    @freeze_time("2025-01-15 12:30:45")
    def test_create_todo_saves_to_dynamodb(self, mock_dynamodb_table):
        """Test that todo is actually saved to DynamoDB"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])
        task_id = body['todo']['taskId']

        # Verify item is in DynamoDB
        result = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )

        items = result['Items']
        assert len(items) == 1
        assert items[0]['taskId'] == task_id
        assert items[0]['title'] == 'Test Task'

    @freeze_time("2025-01-15 12:30:45")
    def test_create_todo_sets_correct_keys(self, mock_dynamodb_table):
        """Test that PK, SK, GSI1PK, and GSI1SK are set correctly"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        # Query DynamoDB to get the saved item
        result = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )

        item = result['Items'][0]
        assert item['PK'] == 'USER#test-user-001'
        assert item['SK'].startswith('TODO#2025-01-15T12:30:45Z#')
        assert item['GSI1PK'] == 'USER#test-user-001'
        assert item['GSI1SK'] == 'DUE#2025-01-20#HIGH'


class TestCreateTodoResponseHeaders:
    """Tests for response headers"""

    def test_response_has_cors_headers(self, mock_dynamodb_table):
        """Test that response includes CORS headers"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_error_response_has_cors_headers(self, mock_dynamodb_table):
        """Test that error responses also include CORS headers"""
        event = {
            'body': json.dumps({'title': 'Missing fields'})
        }

        response = app.lambda_handler(event, None)

        assert 'headers' in response
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestCreateTodoEdgeCases:
    """Tests for edge cases"""

    @freeze_time("2025-01-15 12:30:45")
    def test_create_todo_with_unicode_title(self, mock_dynamodb_table):
        """Test creating todo with unicode characters in title"""
        event = {
            'body': json.dumps({
                'title': 'テストタスク 🎉',
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['todo']['title'] == 'テストタスク 🎉'

    @freeze_time("2025-01-15 12:30:45")
    def test_create_todo_with_very_long_title(self, mock_dynamodb_table):
        """Test creating todo with very long title"""
        long_title = 'A' * 1000
        event = {
            'body': json.dumps({
                'title': long_title,
                'dueDate': '2025-01-20',
                'priority': 'LOW'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['todo']['title'] == long_title

    @freeze_time("2025-01-15 12:30:45")
    def test_create_todo_with_special_characters(self, mock_dynamodb_table):
        """Test creating todo with special characters"""
        event = {
            'body': json.dumps({
                'title': 'Task with "quotes" and \'apostrophes\' & <tags>',
                'description': 'Description with\nnewlines\tand\ttabs',
                'dueDate': '2025-01-20',
                'priority': 'MEDIUM'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'quotes' in body['todo']['title']
        assert 'newlines' in body['todo']['description']

    def test_create_todo_dynamodb_error(self, mock_dynamodb_table):
        """Test handling of DynamoDB errors"""
        event = {
            'body': json.dumps({
                'title': 'Test Task',
                'dueDate': '2025-01-20',
                'priority': 'HIGH'
            })
        }

        # Mock put_item to raise an exception
        with patch.object(mock_dynamodb_table, 'put_item', side_effect=Exception('DynamoDB error')):
            response = app.lambda_handler(event, None)

            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
