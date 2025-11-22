import React, { useState } from 'react';
//import './TodoForm.css';

function TodoForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    dueDate: '',
    priority: 'MEDIUM'
  });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.dueDate) {
      alert('Title and Due Date are required');
      return;
    }

    setSubmitting(true);
    
    try {
      // Convert date to ISO format with time
      const dueDateISO = new Date(formData.dueDate + 'T23:59:59Z').toISOString();
      
      await onSubmit({
        ...formData,
        dueDate: dueDateISO
      });
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        dueDate: '',
        priority: 'MEDIUM'
      });
    } catch (error) {
      console.error('Error submitting form:', error);
      alert('Failed to create todo');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="todo-form-container">
      <h2>➕ Create New Task</h2>
      <form onSubmit={handleSubmit} className="todo-form">
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Enter task title"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Enter task description"
            rows="3"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="dueDate">Due Date *</label>
            <input
              type="date"
              id="dueDate"
              name="dueDate"
              value={formData.dueDate}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
            >
              <option value="HIGH">🔴 High</option>
              <option value="MEDIUM">🟡 Medium</option>
              <option value="LOW">🟢 Low</option>
            </select>
          </div>
        </div>

        <button 
          type="submit" 
          className="submit-btn"
          disabled={submitting}
        >
          {submitting ? 'Creating...' : '✨ Create Task'}
        </button>
      </form>
    </div>
  );
}

export default TodoForm;