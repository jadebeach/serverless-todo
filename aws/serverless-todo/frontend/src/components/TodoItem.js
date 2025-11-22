import React, { useState } from 'react';
//import './TodoItem.css';

function TodoItem({ todo, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({
    title: todo.title,
    description: todo.description,
    priority: todo.priority
  });

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'HIGH': return '🔴';
      case 'MEDIUM': return '🟡';
      case 'LOW': return '🟢';
      default: return '⚪';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP');
  };

  const handleToggleComplete = () => {
    const newStatus = todo.status === 'PENDING' ? 'COMPLETED' : 'PENDING';
    onUpdate(todo.taskId, { status: newStatus });
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancelEdit = () => {
    setEditing(false);
    setEditData({
      title: todo.title,
      description: todo.description,
      priority: todo.priority
    });
  };

  const handleSaveEdit = () => {
    onUpdate(todo.taskId, editData);
    setEditing(false);
  };

  const handleDelete = () => {
    if (window.confirm(`Delete task "${todo.title}"?`)) {
      onDelete(todo.taskId);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  if (editing) {
    return (
      <div className="todo-item editing">
        <div className="edit-form">
          <input
            type="text"
            name="title"
            value={editData.title}
            onChange={handleChange}
            placeholder="Title"
            className="edit-input"
          />
          <textarea
            name="description"
            value={editData.description}
            onChange={handleChange}
            placeholder="Description"
            className="edit-textarea"
            rows="2"
          />
          <select
            name="priority"
            value={editData.priority}
            onChange={handleChange}
            className="edit-select"
          >
            <option value="HIGH">🔴 High</option>
            <option value="MEDIUM">🟡 Medium</option>
            <option value="LOW">🟢 Low</option>
          </select>
          <div className="edit-actions">
            <button onClick={handleSaveEdit} className="save-btn">
              💾 Save
            </button>
            <button onClick={handleCancelEdit} className="cancel-btn">
              ❌ Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`todo-item ${todo.status === 'COMPLETED' ? 'completed' : ''}`}>
      <div className="todo-checkbox">
        <input
          type="checkbox"
          checked={todo.status === 'COMPLETED'}
          onChange={handleToggleComplete}
        />
      </div>
      
      <div className="todo-content">
        <div className="todo-header">
          <h4 className="todo-title">{todo.title}</h4>
          <span className="todo-priority">
            {getPriorityIcon(todo.priority)} {todo.priority}
          </span>
        </div>
        
        {todo.description && (
          <p className="todo-description">{todo.description}</p>
        )}
        
        <div className="todo-meta">
          <span className="todo-date">
            📅 Due: {formatDate(todo.dueDate)}
          </span>
          <span className="todo-created">
            Created: {formatDate(todo.createdAt)}
          </span>
        </div>
      </div>
      
      <div className="todo-actions">
        <button 
          onClick={handleEdit} 
          className="edit-btn"
          title="Edit"
        >
          ✏️
        </button>
        <button 
          onClick={handleDelete} 
          className="delete-btn"
          title="Delete"
        >
          🗑️
        </button>
      </div>
    </div>
  );
}

export default TodoItem;