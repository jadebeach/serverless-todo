import pytest
import json
import os
from unittest.mock import patch
from moto import mock_dynamodb
import boto3
from freezegun import freeze_time
import sys

# Add function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../functions/update_todo'))

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
        'title': 'Original Title',
        'description': 'Original description',
        'dueDate': '2025-01-20',
        'priority': 'HIGH',
        'status': 'PENDING',
        'createdAt': '2025-01-15T10:00:00Z',
        'updatedAt': '2025-01-15T10:00:00Z'
    }

    mock_dynamodb_table.put_item(Item=todo)
    return todo


class TestUpdateTodoValidation:
    """Tests for input validation"""

    def test_missing_task_id(self, sample_todo):
        """Test error when taskId is missing from path"""
        event = {
            'pathParameters': {},
            'body': json.dumps({'title': 'New Title'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'taskId' in body['error']

    def test_none_path_parameters(self, sample_todo):
        """Test error when pathParameters is None"""
        event = {
            'pathParameters': None,
            'body': json.dumps({'title': 'New Title'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400

    def test_task_not_found(self, mock_dynamodb_table):
        """Test error when task doesn't exist"""
        event = {
            'pathParameters': {'taskId': 'non-existent-task'},
            'body': json.dumps({'title': 'New Title'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error'].lower()

    def test_no_fields_to_update(self, sample_todo):
        """Test error when body contains no updatable fields"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'No fields to update' in body['error']

    def test_invalid_priority(self, sample_todo):
        """Test error when priority is invalid"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'priority': 'URGENT'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'HIGH, MEDIUM, or LOW' in body['error']

    def test_invalid_status(self, sample_todo):
        """Test error when status is invalid"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'status': 'IN_PROGRESS'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'PENDING or COMPLETED' in body['error']

    def test_invalid_json(self, sample_todo):
        """Test error when request body is invalid JSON"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': 'not valid json {'
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'JSON' in body['error']


class TestUpdateTodoSingleField:
    """Tests for updating single fields"""

    @freeze_time("2025-01-16 14:30:00")
    def test_update_title_only(self, sample_todo):
        """Test updating only the title"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'title': 'Updated Title'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['title'] == 'Updated Title'
        assert body['task']['description'] == 'Original description'
        assert body['task']['updatedAt'] == '2025-01-16T14:30:00Z'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_description_only(self, sample_todo):
        """Test updating only the description"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'description': 'Updated description'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['title'] == 'Original Title'
        assert body['task']['description'] == 'Updated description'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_due_date_only(self, sample_todo):
        """Test updating only the due date"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'dueDate': '2025-01-25'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['dueDate'] == '2025-01-25'
        # Priority should remain the same
        assert body['task']['priority'] == 'HIGH'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_priority_only(self, sample_todo):
        """Test updating only the priority"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'priority': 'LOW'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['priority'] == 'LOW'
        # Due date should remain the same
        assert body['task']['dueDate'] == '2025-01-20'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_status_only(self, sample_todo):
        """Test updating only the status"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'status': 'COMPLETED'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['status'] == 'COMPLETED'


class TestUpdateTodoMultipleFields:
    """Tests for updating multiple fields"""

    @freeze_time("2025-01-16 14:30:00")
    def test_update_title_and_description(self, sample_todo):
        """Test updating title and description together"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({
                'title': 'New Title',
                'description': 'New description'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['title'] == 'New Title'
        assert body['task']['description'] == 'New description'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_priority_and_due_date(self, sample_todo):
        """Test updating priority and due date together"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({
                'priority': 'MEDIUM',
                'dueDate': '2025-01-30'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['priority'] == 'MEDIUM'
        assert body['task']['dueDate'] == '2025-01-30'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_all_fields(self, sample_todo):
        """Test updating all updatable fields"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({
                'title': 'Completely New Title',
                'description': 'Completely new description',
                'dueDate': '2025-02-01',
                'priority': 'LOW',
                'status': 'COMPLETED'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['title'] == 'Completely New Title'
        assert body['task']['description'] == 'Completely new description'
        assert body['task']['dueDate'] == '2025-02-01'
        assert body['task']['priority'] == 'LOW'
        assert body['task']['status'] == 'COMPLETED'
        assert body['task']['updatedAt'] == '2025-01-16T14:30:00Z'


class TestUpdateTodoGSI1SK:
    """Tests for GSI1SK updates"""

    @freeze_time("2025-01-16 14:30:00")
    def test_update_due_date_updates_gsi1sk(self, sample_todo, mock_dynamodb_table):
        """Test that updating due date updates GSI1SK"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'dueDate': '2025-01-30'})
        }

        response = app.lambda_handler(event, None)
        assert response['statusCode'] == 200

        # Verify GSI1SK is updated in DynamoDB
        result = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )

        item = result['Items'][0]
        # GSI1SK should be updated with new due date
        assert item['GSI1SK'] == 'DUE#2025-01-30#HIGH'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_priority_updates_gsi1sk(self, sample_todo, mock_dynamodb_table):
        """Test that updating priority updates GSI1SK"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'priority': 'LOW'})
        }

        response = app.lambda_handler(event, None)
        assert response['statusCode'] == 200

        # Verify GSI1SK is updated
        result = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )

        item = result['Items'][0]
        # GSI1SK should be updated with new priority
        assert item['GSI1SK'] == 'DUE#2025-01-20#LOW'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_both_due_date_and_priority_updates_gsi1sk(self, sample_todo, mock_dynamodb_table):
        """Test that updating both due date and priority updates GSI1SK correctly"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({
                'dueDate': '2025-02-15',
                'priority': 'MEDIUM'
            })
        }

        response = app.lambda_handler(event, None)
        assert response['statusCode'] == 200

        # Verify GSI1SK is updated with both changes
        result = mock_dynamodb_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'USER#test-user-001'}
        )

        item = result['Items'][0]
        assert item['GSI1SK'] == 'DUE#2025-02-15#MEDIUM'


class TestUpdateTodoTimestamp:
    """Tests for updatedAt timestamp"""

    @freeze_time("2025-01-16 14:30:45")
    def test_updated_at_is_set(self, sample_todo):
        """Test that updatedAt is set to current time"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'title': 'New Title'})
        }

        response = app.lambda_handler(event, None)
        body = json.loads(response['body'])

        assert body['task']['updatedAt'] == '2025-01-16T14:30:45Z'
        assert body['task']['createdAt'] == '2025-01-15T10:00:00Z'  # Should not change

    @freeze_time("2025-01-16 14:30:45")
    def test_updated_at_changes_on_each_update(self, sample_todo):
        """Test that updatedAt changes with each update"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'title': 'Title 1'})
        }

        response1 = app.lambda_handler(event, None)
        body1 = json.loads(response1['body'])

        # All updates at same frozen time will have same timestamp
        assert body1['task']['updatedAt'] == '2025-01-16T14:30:45Z'


class TestUpdateTodoPriorityLevels:
    """Tests for all priority levels"""

    @freeze_time("2025-01-16 14:30:00")
    @pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
    def test_update_to_each_priority_level(self, sample_todo, priority):
        """Test updating to each valid priority level"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'priority': priority})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['priority'] == priority


class TestUpdateTodoStatusLevels:
    """Tests for status transitions"""

    @freeze_time("2025-01-16 14:30:00")
    def test_update_pending_to_completed(self, sample_todo):
        """Test updating status from PENDING to COMPLETED"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'status': 'COMPLETED'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['status'] == 'COMPLETED'

    @freeze_time("2025-01-16 14:30:00")
    def test_update_completed_to_pending(self, mock_dynamodb_table):
        """Test updating status from COMPLETED to PENDING"""
        # Create a completed task
        todo = {
            'PK': 'USER#test-user-001',
            'SK': 'TODO#2025-01-15T10:00:00Z#task-456',
            'GSI1PK': 'USER#test-user-001',
            'GSI1SK': 'DUE#2025-01-20#HIGH',
            'taskId': 'task-456',
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
            'pathParameters': {'taskId': 'task-456'},
            'body': json.dumps({'status': 'PENDING'})
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['status'] == 'PENDING'


class TestUpdateTodoResponseHeaders:
    """Tests for response headers"""

    def test_response_has_cors_headers(self, sample_todo):
        """Test that response includes CORS headers"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'title': 'New Title'})
        }

        response = app.lambda_handler(event, None)

        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_error_response_has_cors_headers(self, sample_todo):
        """Test that error responses also include CORS headers"""
        event = {
            'pathParameters': {'taskId': 'non-existent'},
            'body': json.dumps({'title': 'New Title'})
        }

        response = app.lambda_handler(event, None)

        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestUpdateTodoEdgeCases:
    """Tests for edge cases"""

    @freeze_time("2025-01-16 14:30:00")
    def test_update_with_unicode_characters(self, sample_todo):
        """Test updating with unicode characters"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({
                'title': 'タイトル 🎉',
                'description': 'テスト説明 ✨'
            })
        }

        response = app.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['task']['title'] == 'タイトル 🎉'
        assert body['task']['description'] == 'テスト説明 ✨'

    def test_update_dynamodb_error(self, sample_todo, mock_dynamodb_table):
        """Test handling of DynamoDB errors"""
        event = {
            'pathParameters': {'taskId': 'task-123'},
            'body': json.dumps({'title': 'New Title'})
        }

        # Mock update_item to raise an exception
        with patch.object(mock_dynamodb_table, 'update_item', side_effect=Exception('DynamoDB error')):
            response = app.lambda_handler(event, None)

            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body


class TestFindTaskHelper:
    """Tests for find_task helper function"""

    def test_find_task_exists(self, sample_todo):
        """Test finding an existing task"""
        result = app.find_task('test-user-001', 'task-123')

        assert result is not None
        assert result['taskId'] == 'task-123'
        assert result['title'] == 'Original Title'

    def test_find_task_not_found(self, mock_dynamodb_table):
        """Test finding a non-existent task"""
        result = app.find_task('test-user-001', 'non-existent')

        assert result is None

    def test_find_task_handles_errors(self, mock_dynamodb_table):
        """Test that find_task handles DynamoDB errors gracefully"""
        with patch.object(mock_dynamodb_table, 'query', side_effect=Exception('DynamoDB error')):
            result = app.find_task('test-user-001', 'any-task')

            assert result is None
