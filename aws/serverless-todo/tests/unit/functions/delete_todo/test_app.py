import pytest
import json
import os
from unittest.mock import patch
from moto import mock_dynamodb
import boto3
import sys

# Add function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../functions/delete_todo'))

import app


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table"""
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
def sample_todo(mock_dynamodb_table):
    """Insert a sample todo"""
    todo = {
        'PK': 'USER#test-user-001',
        'SK': 'TODO#2025-01-15T10:00:00Z#task-123',
        'GSI1PK': 'USER#test-user-001',
        'GSI1SK': 'DUE#2025-01-20#HIGH',
        'taskId': 'task-123',
        'title': 'Test Task',
        'description': 'Test description',
        'dueDate': '2025-01-20',
        'priority': 'HIGH',
        'status': 'PENDING',
        'createdAt': '2025-01-15T10:00:00Z',
        'updatedAt': '2025-01-15T10:00:00Z'
    }

    mock_dynamodb_table.put_item(Item=todo)
    return todo


class TestDeleteTodoValidation:
    """Tests for input validation"""

    def test_missing_task_id(self, sample_todo):
        """Test error when taskId is missing from path"""
        event = {
            'pathParameters': {}
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'taskId' in body['error']

    def test_none_path_parameters(self, sample_todo):
        """Test error when pathParameters is None"""
        event = {
            'pathParameters': None
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400

    def test_empty_task_id(self, sample_todo):
        """Test error when taskId is empty string"""
        event = {
            'pathParameters': {'taskId': ''}
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400

    def test_task_not_found(self, mock_dynamodb_table):
        """Test error when task doesn't exist"""
        event = {
            'pathParameters': {'taskId': 'non-existent-task'}
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error'].lower()
        assert 'non-existent-task' in body['taskId']


class TestDeleteTodoSuccess:
    """Tests for successful deletion"""

    def test_delete_existing_task(self, sample_todo):
        """Test deleting an existing task"""
        event = {
            'pathParameters': {'taskId': 'task-123'}
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'message' in body
        assert 'deleted successfully' in body['message'].lower()
        assert body['taskId'] == 'task-123'

    def test_delete_task_removes_from_dynamodb(self, sample_todo, mock_dynamodb_table):
        """Test that task is actually removed from DynamoDB"""
        event = {
            'pathParameters': {'taskId': 'task-123'}
        }

        # Verify task exists before deletion
        result_before = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )
        assert len(result_before['Items']) == 1

        # Delete the task
        response = app.lambda_handler(event, None)
        assert response['statusCode'] == 200

        # Verify task is deleted
        result_after = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )
        assert len(result_after['Items']) == 0

    def test_delete_task_with_correct_keys(self, sample_todo, mock_dynamodb_table):
        """Test that delete uses correct PK and SK"""
        event = {
            'pathParameters': {'taskId': 'task-123'}
        }

        response = app.lambda_handler(event, None)
        assert response['statusCode'] == 200

        # Verify specific item with PK and SK is deleted
        from boto3.dynamodb.conditions import Key
        result = mock_dynamodb_table.query(
            KeyConditionExpression=Key('PK').eq('USER#test-user-001') & Key('SK').begins_with('TODO#2025-01-15T10:00:00Z#task-123')
        )
        assert len(result['Items']) == 0


class TestDeleteTodoMultipleTasks:
    """Tests with multiple tasks"""

    def test_delete_one_task_leaves_others(self, mock_dynamodb_table):
        """Test deleting one task doesn't affect others"""
        # Create multiple tasks
        todos = [
            {
                'PK': 'USER#test-user-001',
                'SK': f'TODO#2025-01-15T10:00:00Z#task-{i}',
                'GSI1PK': 'USER#test-user-001',
                'GSI1SK': f'DUE#2025-01-20#HIGH',
                'taskId': f'task-{i}',
                'title': f'Task {i}',
                'description': '',
                'dueDate': '2025-01-20',
                'priority': 'HIGH',
                'status': 'PENDING',
                'createdAt': '2025-01-15T10:00:00Z',
                'updatedAt': '2025-01-15T10:00:00Z'
            }
            for i in range(1, 4)
        ]

        for todo in todos:
            mock_dynamodb_table.put_item(Item=todo)

        # Delete task-2
        event = {
            'pathParameters': {'taskId': 'task-2'}
        }

        response = app.lambda_handler(event, None)
        assert response['statusCode'] == 200

        # Verify only task-2 is deleted
        result = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )

        assert len(result['Items']) == 2
        task_ids = [item['taskId'] for item in result['Items']]
        assert 'task-1' in task_ids
        assert 'task-3' in task_ids
        assert 'task-2' not in task_ids

    def test_delete_completed_task(self, mock_dynamodb_table):
        """Test deleting a completed task"""
        todo = {
            'PK': 'USER#test-user-001',
            'SK': 'TODO#2025-01-15T10:00:00Z#completed-task',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-20#HIGH',
            'taskId': 'completed-task',
            'title': 'Completed Task',
            'description': '',
            'dueDate': '2025-01-20',
            'priority': 'HIGH',
            'status': 'COMPLETED',
            'createdAt': '2025-01-15T10:00:00Z',
            'updatedAt': '2025-01-15T11:00:00Z'
        }
        mock_dynamodb_table.put_item(Item=todo)

        event = {
            'pathParameters': {'taskId': 'completed-task'}
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['taskId'] == 'completed-task'


class TestDeleteTodoResponseHeaders:
    """Tests for response headers"""

    def test_response_has_cors_headers(self, sample_todo):
        """Test that response includes CORS headers"""
        event = {
            'pathParameters': {'taskId': 'task-123'}
        }

        response = app.lambda_handler(event, None)

        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_error_response_has_cors_headers(self, sample_todo):
        """Test that error responses also include CORS headers"""
        event = {
            'pathParameters': {'taskId': 'non-existent'}
        }

        response = app.lambda_handler(event, None)

        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestDeleteTodoErrorHandling:
    """Tests for error handling"""

    def test_delete_dynamodb_query_error(self, mock_dynamodb_table):
        """Test handling of DynamoDB query errors"""
        # Create a task first
        todo = {
            'PK': 'USER#test-user-001',
            'SK': 'TODO#2025-01-15T10:00:00Z#task-999',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-20#HIGH',
            'taskId': 'task-999',
            'title': 'Test Task',
            'description': '',
            'dueDate': '2025-01-20',
            'priority': 'HIGH',
            'status': 'PENDING',
            'createdAt': '2025-01-15T10:00:00Z',
            'updatedAt': '2025-01-15T10:00:00Z'
        }
        mock_dynamodb_table.put_item(Item=todo)

        event = {
            'pathParameters': {'taskId': 'task-999'}
        }

        # Mock query to raise an exception
        with patch.object(mock_dynamodb_table, 'query', side_effect=Exception('DynamoDB query error')):
            response = app.lambda_handler(event, None)

            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body

    def test_delete_dynamodb_delete_error(self, sample_todo, mock_dynamodb_table):
        """Test handling of DynamoDB delete errors"""
        event = {
            'pathParameters': {'taskId': 'task-123'}
        }

        # Mock delete_item to raise an exception
        original_query = mock_dynamodb_table.query

        def query_then_fail(*args, **kwargs):
            # Let query succeed first time to find the task
            return original_query(*args, **kwargs)

        with patch.object(mock_dynamodb_table, 'query', side_effect=query_then_fail):
            with patch.object(mock_dynamodb_table, 'delete_item', side_effect=Exception('DynamoDB delete error')):
                response = app.lambda_handler(event, None)

                assert response['statusCode'] == 500
                body = json.loads(response['body'])
                assert 'error' in body


class TestDeleteTodoEdgeCases:
    """Tests for edge cases"""

    def test_delete_task_with_special_characters_in_id(self, mock_dynamodb_table):
        """Test deleting task with special characters in ID"""
        task_id = 'task-with-special-chars-@#$'
        todo = {
            'PK': 'USER#test-user-001',
            'SK': f'TODO#2025-01-15T10:00:00Z#{task_id}',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-20#HIGH',
            'taskId': task_id,
            'title': 'Test Task',
            'description': '',
            'dueDate': '2025-01-20',
            'priority': 'HIGH',
            'status': 'PENDING',
            'createdAt': '2025-01-15T10:00:00Z',
            'updatedAt': '2025-01-15T10:00:00Z'
        }
        mock_dynamodb_table.put_item(Item=todo)

        event = {
            'pathParameters': {'taskId': task_id}
        }

        response = app.lambda_handler(event, None)

        # Should handle special characters correctly
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['taskId'] == task_id

    def test_delete_task_with_uuid(self, mock_dynamodb_table):
        """Test deleting task with UUID format ID"""
        task_id = '550e8400-e29b-41d4-a716-446655440000'
        todo = {
            'PK': 'USER#test-user-001',
            'SK': f'TODO#2025-01-15T10:00:00Z#{task_id}',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-20#HIGH',
            'taskId': task_id,
            'title': 'Test Task',
            'description': '',
            'dueDate': '2025-01-20',
            'priority': 'HIGH',
            'status': 'PENDING',
            'createdAt': '2025-01-15T10:00:00Z',
            'updatedAt': '2025-01-15T10:00:00Z'
        }
        mock_dynamodb_table.put_item(Item=todo)

        event = {
            'pathParameters': {'taskId': task_id}
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['taskId'] == task_id


class TestFindTaskHelper:
    """Tests for find_task helper function"""

    def test_find_task_exists(self, sample_todo):
        """Test finding an existing task"""
        result = app.find_task('test-user-001', 'task-123')

        assert result is not None
        assert result['taskId'] == 'task-123'
        assert result['title'] == 'Test Task'

    def test_find_task_not_found(self, mock_dynamodb_table):
        """Test finding a non-existent task"""
        result = app.find_task('test-user-001', 'non-existent')

        assert result is None

    def test_find_task_handles_errors(self, mock_dynamodb_table):
        """Test that find_task handles DynamoDB errors gracefully"""
        with patch.object(mock_dynamodb_table, 'query', side_effect=Exception('DynamoDB error')):
            result = app.find_task('test-user-001', 'any-task')

            assert result is None

    def test_find_task_with_multiple_tasks(self, mock_dynamodb_table):
        """Test finding specific task among multiple tasks"""
        # Create multiple tasks
        for i in range(1, 4):
            todo = {
                'PK': 'USER#test-user-001',
                'SK': f'TODO#2025-01-15T10:00:0{i}Z#task-{i}',
                'GSI1PK': 'USER#test-user-001',
                'GSI1SK': 'DUE#2025-01-20#HIGH',
                'taskId': f'task-{i}',
                'title': f'Task {i}',
                'description': '',
                'dueDate': '2025-01-20',
                'priority': 'HIGH',
                'status': 'PENDING',
                'createdAt': f'2025-01-15T10:00:0{i}Z',
                'updatedAt': f'2025-01-15T10:00:0{i}Z'
            }
            mock_dynamodb_table.put_item(Item=todo)

        result = app.find_task('test-user-001', 'task-2')

        assert result is not None
        assert result['taskId'] == 'task-2'
        assert result['title'] == 'Task 2'
