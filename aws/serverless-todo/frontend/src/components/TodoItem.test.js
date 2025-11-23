import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TodoItem from './TodoItem';

const mockPendingTodo = {
  taskId: '123',
  title: 'Test Task',
  description: 'Test Description',
  dueDate: '2025-01-20T00:00:00Z',
  priority: 'HIGH',
  status: 'PENDING',
  createdAt: '2025-01-15T10:00:00Z',
  updatedAt: '2025-01-15T10:00:00Z'
};

const mockCompletedTodo = {
  ...mockPendingTodo,
  status: 'COMPLETED'
};

describe('TodoItem Component', () => {
  let mockOnUpdate, mockOnDelete;

  beforeEach(() => {
    mockOnUpdate = jest.fn();
    mockOnDelete = jest.fn();
    jest.spyOn(window, 'confirm').mockImplementation(() => true);
  });

  afterEach(() => {
    window.confirm.mockRestore();
  });

  describe('Display Mode', () => {
    test('renders todo title', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    test('renders todo description', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      expect(screen.getByText('Test Description')).toBeInTheDocument();
    });

    test('does not render description when empty', () => {
      const todoWithoutDesc = { ...mockPendingTodo, description: '' };
      render(<TodoItem todo={todoWithoutDesc} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      expect(screen.queryByText('Test Description')).not.toBeInTheDocument();
    });

    test('renders priority with icon', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      expect(screen.getByText(/HIGH/i)).toBeInTheDocument();
      expect(screen.getByText(/🔴/)).toBeInTheDocument();
    });

    test('renders all priority levels correctly', () => {
      const priorities = [
        { priority: 'HIGH', icon: '🔴' },
        { priority: 'MEDIUM', icon: '🟡' },
        { priority: 'LOW', icon: '🟢' }
      ];

      priorities.forEach(({ priority, icon }) => {
        const todo = { ...mockPendingTodo, priority };
        const { rerender } = render(<TodoItem todo={todo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

        expect(screen.getByText(new RegExp(priority, 'i'))).toBeInTheDocument();
        expect(screen.getByText(icon)).toBeInTheDocument();

        rerender(<div />);
      });
    });

    test('renders due date', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      expect(screen.getByText(/Due:/i)).toBeInTheDocument();
    });

    test('renders created date', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      expect(screen.getByText(/Created:/i)).toBeInTheDocument();
    });

    test('renders checkbox for completion status', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
      expect(checkbox.checked).toBe(false);
    });

    test('checkbox is checked for completed tasks', () => {
      render(<TodoItem todo={mockCompletedTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox.checked).toBe(true);
    });

    test('renders edit button', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const editButton = screen.getByTitle('Edit');
      expect(editButton).toBeInTheDocument();
    });

    test('renders delete button', () => {
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const deleteButton = screen.getByTitle('Delete');
      expect(deleteButton).toBeInTheDocument();
    });
  });

  describe('Completion Toggle', () => {
    test('calls onUpdate with COMPLETED when pending task is checked', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);

      expect(mockOnUpdate).toHaveBeenCalledWith('123', { status: 'COMPLETED' });
    });

    test('calls onUpdate with PENDING when completed task is unchecked', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockCompletedTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);

      expect(mockOnUpdate).toHaveBeenCalledWith('123', { status: 'PENDING' });
    });
  });

  describe('Edit Mode', () => {
    test('enters edit mode when edit button clicked', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const editButton = screen.getByTitle('Edit');
      await user.click(editButton);

      expect(screen.getByPlaceholderText('Title')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Description')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Save/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
    });

    test('edit inputs have current values', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));

      expect(screen.getByPlaceholderText('Title')).toHaveValue('Test Task');
      expect(screen.getByPlaceholderText('Description')).toHaveValue('Test Description');
      expect(screen.getByRole('combobox')).toHaveValue('HIGH');
    });

    test('updates edit inputs when changed', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));

      const titleInput = screen.getByPlaceholderText('Title');
      await user.clear(titleInput);
      await user.type(titleInput, 'Updated Title');

      expect(titleInput).toHaveValue('Updated Title');
    });

    test('saves changes when save button clicked', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));

      const titleInput = screen.getByPlaceholderText('Title');
      await user.clear(titleInput);
      await user.type(titleInput, 'Updated Title');

      await user.click(screen.getByRole('button', { name: /Save/i }));

      expect(mockOnUpdate).toHaveBeenCalledWith('123', {
        title: 'Updated Title',
        description: 'Test Description',
        priority: 'HIGH'
      });
    });

    test('exits edit mode after save', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));
      await user.click(screen.getByRole('button', { name: /Save/i }));

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Title')).not.toBeInTheDocument();
      });
    });

    test('cancels edit and restores original values', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));

      const titleInput = screen.getByPlaceholderText('Title');
      await user.clear(titleInput);
      await user.type(titleInput, 'Changed Title');

      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      // Should exit edit mode
      expect(screen.queryByPlaceholderText('Title')).not.toBeInTheDocument();
      // Original title should be shown
      expect(screen.getByText('Test Task')).toBeInTheDocument();
      // onUpdate should not have been called
      expect(mockOnUpdate).not.toHaveBeenCalled();
    });

    test('can update description in edit mode', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));

      const descInput = screen.getByPlaceholderText('Description');
      await user.clear(descInput);
      await user.type(descInput, 'New Description');

      await user.click(screen.getByRole('button', { name: /Save/i }));

      expect(mockOnUpdate).toHaveBeenCalledWith('123', {
        title: 'Test Task',
        description: 'New Description',
        priority: 'HIGH'
      });
    });

    test('can update priority in edit mode', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));

      const prioritySelect = screen.getByRole('combobox');
      await user.selectOptions(prioritySelect, 'LOW');

      await user.click(screen.getByRole('button', { name: /Save/i }));

      expect(mockOnUpdate).toHaveBeenCalledWith('123', {
        title: 'Test Task',
        description: 'Test Description',
        priority: 'LOW'
      });
    });
  });

  describe('Delete Functionality', () => {
    test('shows confirmation dialog when delete clicked', async () => {
      const user = userEvent.setup();
      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Delete'));

      expect(window.confirm).toHaveBeenCalledWith('Delete task "Test Task"?');
    });

    test('calls onDelete when confirmed', async () => {
      const user = userEvent.setup();
      window.confirm.mockReturnValue(true);

      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Delete'));

      expect(mockOnDelete).toHaveBeenCalledWith('123');
    });

    test('does not delete when cancelled', async () => {
      const user = userEvent.setup();
      window.confirm.mockReturnValue(false);

      render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Delete'));

      expect(mockOnDelete).not.toHaveBeenCalled();
    });
  });

  describe('CSS Classes', () => {
    test('applies completed class for completed tasks', () => {
      const { container } = render(<TodoItem todo={mockCompletedTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const todoItem = container.querySelector('.todo-item');
      expect(todoItem).toHaveClass('completed');
    });

    test('does not apply completed class for pending tasks', () => {
      const { container } = render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      const todoItem = container.querySelector('.todo-item');
      expect(todoItem).not.toHaveClass('completed');
    });

    test('applies editing class in edit mode', async () => {
      const user = userEvent.setup();
      const { container } = render(<TodoItem todo={mockPendingTodo} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);

      await user.click(screen.getByTitle('Edit'));

      const todoItem = container.querySelector('.todo-item');
      expect(todoItem).toHaveClass('editing');
    });
  });
});
