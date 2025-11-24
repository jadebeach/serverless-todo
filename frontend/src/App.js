import React, { useState, useEffect } from 'react';
import { Amplify } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import { fetchAuthSession } from 'aws-amplify/auth';
import '@aws-amplify/ui-react/styles.css';
import awsConfig from './aws-config';
import TodoList from './components/TodoList';
import TodoForm from './components/TodoForm';
import './App.css';

// Configure Amplify
Amplify.configure(awsConfig);

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch todos from API
  const fetchTodos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get ID token from Cognito
      const session = await fetchAuthSession();
      const idToken = session.tokens?.idToken?.toString();
      
      if (!idToken) {
        throw new Error('No authentication token available');
      }

      // Call API
      const response = await fetch(`${awsConfig.API.REST.TodoAPI.endpoint}/todos`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch todos: ${response.statusText}`);
      }

      const data = await response.json();
      setTodos(data.items || []);
    } catch (err) {
      console.error('Error fetching todos:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Create todo
  const createTodo = async (todoData) => {
    try {
      const session = await fetchAuthSession();
      const idToken = session.tokens?.idToken?.toString();

      const response = await fetch(`${awsConfig.API.REST.TodoAPI.endpoint}/todos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(todoData)
      });

      if (!response.ok) {
        throw new Error(`Failed to create todo: ${response.statusText}`);
      }

      // Refresh list
      await fetchTodos();
    } catch (err) {
      console.error('Error creating todo:', err);
      setError(err.message);
    }
  };

  // Update todo
  const updateTodo = async (taskId, updates) => {
    try {
      const session = await fetchAuthSession();
      const idToken = session.tokens?.idToken?.toString();

      const response = await fetch(`${awsConfig.API.REST.TodoAPI.endpoint}/todos/${taskId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error(`Failed to update todo: ${response.statusText}`);
      }

      // Refresh list
      await fetchTodos();
    } catch (err) {
      console.error('Error updating todo:', err);
      setError(err.message);
    }
  };

  // Delete todo
  const deleteTodo = async (taskId) => {
    try {
      const session = await fetchAuthSession();
      const idToken = session.tokens?.idToken?.toString();

      const response = await fetch(`${awsConfig.API.REST.TodoAPI.endpoint}/todos/${taskId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to delete todo: ${response.statusText}`);
      }

      // Refresh list
      await fetchTodos();
    } catch (err) {
      console.error('Error deleting todo:', err);
      setError(err.message);
    }
  };

  return (
    <Authenticator>
      {({ signOut, user }) => (
        <div className="App">
          <header className="App-header">
            <h1>📝 Serverless Todo App</h1>
            <div className="user-info">
              <span>👤 {user?.signInDetails?.loginId}</span>
              <button onClick={signOut} className="sign-out-btn">
                Sign Out
              </button>
            </div>
          </header>

          <main className="App-main">
            {error && (
              <div className="error-message">
                ⚠️ {error}
              </div>
            )}

            <TodoForm onSubmit={createTodo} />
            
            <TodoList
              todos={todos}
              loading={loading}
              onUpdate={updateTodo}
              onDelete={deleteTodo}
              onRefresh={fetchTodos}
            />
          </main>
        </div>
      )}
    </Authenticator>
  );
}

export default App;