import React, { useEffect } from 'react';
import TodoItem from './TodoItem';
//import './TodoList.css';

function TodoList({ todos, loading, onUpdate, onDelete, onRefresh }) {
  // Load todos on mount
  useEffect(() => {
    onRefresh();
  }, []);

  if (loading) {
    return (
      <div className="todo-list-container">
        <div className="loading">⏳ Loading tasks...</div>
      </div>
    );
  }

  if (todos.length === 0) {
    return (
      <div className="todo-list-container">
        <div className="empty-state">
          <h3>📭 No tasks yet</h3>
          <p>Create your first task above to get started!</p>
        </div>
      </div>
    );
  }

  // Separate completed and pending tasks
  const pendingTodos = todos.filter(todo => todo.status === 'PENDING');
  const completedTodos = todos.filter(todo => todo.status === 'COMPLETED');

  return (
    <div className="todo-list-container">
      <div className="list-header">
        <h2>📋 My Tasks ({todos.length})</h2>
        <button onClick={onRefresh} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {pendingTodos.length > 0 && (
        <div className="todo-section">
          <h3 className="section-title">
            ⏰ Pending ({pendingTodos.length})
          </h3>
          <div className="todo-list">
            {pendingTodos.map(todo => (
              <TodoItem
                key={todo.taskId}
                todo={todo}
                onUpdate={onUpdate}
                onDelete={onDelete}
              />
            ))}
          </div>
        </div>
      )}

      {completedTodos.length > 0 && (
        <div className="todo-section">
          <h3 className="section-title">
            ✅ Completed ({completedTodos.length})
          </h3>
          <div className="todo-list">
            {completedTodos.map(todo => (
              <TodoItem
                key={todo.taskId}
                todo={todo}
                onUpdate={onUpdate}
                onDelete={onDelete}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default TodoList;