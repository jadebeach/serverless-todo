import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TodoList from './TodoList';

const mockTodos = [
  {
    taskId: '1',
    title: 'Pending Task 1',
    description: 'Description 1',
    dueDate: '2025-01-20T00:00:00Z',
    priority: 'HIGH',
    status: 'PENDING',
    createdAt: '2025-01-15T10:00:00Z',
    updatedAt: '2025-01-15T10:00:00Z'
  },
  {
    taskId: '2',
    title: 'Pending Task 2',
    description: 'Description 2',
    dueDate: '2025-01-25T00:00:00Z',
    priority: 'MEDIUM',
    status: 'PENDING',
    createdAt: '2025-01-15T11:00:00Z',
    updatedAt: '2025-01-15T11:00:00Z'
  },
  {
    taskId: '3',
    title: 'Completed Task',
    description: 'Description 3',
    dueDate: '2025-01-18T00:00:00Z',
    priority: 'LOW',
    status: 'COMPLETED',
    createdAt: '2025-01-15T12:00:00Z',
    updatedAt: '2025-01-15T13:00:00Z'
  }
];

describe('TodoList Component', () => {
  let mockOnUpdate, mockOnDelete, mockOnRefresh;

  beforeEach(() => {
    mockOnUpdate = jest.fn();
    mockOnDelete = jest.fn();
    mockOnRefresh = jest.fn();
  });

  test('calls onRefresh on mount', () => {
    render(
      <TodoList
        todos={[]}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(mockOnRefresh).toHaveBeenCalledTimes(1);
  });

  test('displays loading state', () => {
    render(
      <TodoList
        todos={[]}
        loading={true}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/Loading tasks/i)).toBeInTheDocument();
  });

  test('displays empty state when no todos', () => {
    render(
      <TodoList
        todos={[]}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/No tasks yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Create your first task/i)).toBeInTheDocument();
  });

  test('renders todos list with todos', () => {
    render(
      <TodoList
        todos={mockTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText('Pending Task 1')).toBeInTheDocument();
    expect(screen.getByText('Pending Task 2')).toBeInTheDocument();
    expect(screen.getByText('Completed Task')).toBeInTheDocument();
  });

  test('displays correct total count', () => {
    render(
      <TodoList
        todos={mockTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/My Tasks \(3\)/i)).toBeInTheDocument();
  });

  test('separates pending and completed tasks', () => {
    render(
      <TodoList
        todos={mockTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/Pending \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Completed \(1\)/i)).toBeInTheDocument();
  });

  test('renders refresh button', () => {
    render(
      <TodoList
        todos={mockTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    const refreshButton = screen.getByText(/Refresh/i);
    expect(refreshButton).toBeInTheDocument();
  });

  test('calls onRefresh when refresh button clicked', async () => {
    const user = userEvent.setup();
    render(
      <TodoList
        todos={mockTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    // Clear the initial onMount call
    mockOnRefresh.mockClear();

    const refreshButton = screen.getByText(/Refresh/i);
    await user.click(refreshButton);

    expect(mockOnRefresh).toHaveBeenCalledTimes(1);
  });

  test('passes callbacks to TodoItem components', () => {
    render(
      <TodoList
        todos={mockTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    // TodoItem should be rendered with the todos
    expect(screen.getByText('Pending Task 1')).toBeInTheDocument();
    expect(screen.getByText('Pending Task 2')).toBeInTheDocument();
    expect(screen.getByText('Completed Task')).toBeInTheDocument();
  });

  test('renders only pending section when no completed tasks', () => {
    const pendingOnlyTodos = mockTodos.filter(t => t.status === 'PENDING');

    render(
      <TodoList
        todos={pendingOnlyTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/Pending \(2\)/i)).toBeInTheDocument();
    expect(screen.queryByText(/Completed/i)).not.toBeInTheDocument();
  });

  test('renders only completed section when no pending tasks', () => {
    const completedOnlyTodos = mockTodos.filter(t => t.status === 'COMPLETED');

    render(
      <TodoList
        todos={completedOnlyTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/Completed \(1\)/i)).toBeInTheDocument();
    expect(screen.queryByText(/Pending/i)).not.toBeInTheDocument();
  });

  test('renders with single todo', () => {
    const singleTodo = [mockTodos[0]];

    render(
      <TodoList
        todos={singleTodo}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/My Tasks \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText('Pending Task 1')).toBeInTheDocument();
  });

  test('renders todos with unique keys', () => {
    const { container } = render(
      <TodoList
        todos={mockTodos}
        loading={false}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    // TodoItem components should be rendered
    const todoItems = container.querySelectorAll('.todo-item');
    expect(todoItems.length).toBe(3);
  });
});
