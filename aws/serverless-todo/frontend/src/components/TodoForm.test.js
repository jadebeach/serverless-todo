import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TodoForm from './TodoForm';

describe('TodoForm Component', () => {
  let mockOnSubmit;

  beforeEach(() => {
    mockOnSubmit = jest.fn().mockResolvedValue(undefined);
    jest.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    window.alert.mockRestore();
  });

  test('renders form with all fields', () => {
    render(<TodoForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Due Date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Priority/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Task/i })).toBeInTheDocument();
  });

  test('renders with default priority set to MEDIUM', () => {
    render(<TodoForm onSubmit={mockOnSubmit} />);

    const prioritySelect = screen.getByLabelText(/Priority/i);
    expect(prioritySelect.value).toBe('MEDIUM');
  });

  test('updates title field when user types', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    const titleInput = screen.getByLabelText(/Title/i);
    await user.type(titleInput, 'New Task Title');

    expect(titleInput.value).toBe('New Task Title');
  });

  test('updates description field when user types', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    const descriptionInput = screen.getByLabelText(/Description/i);
    await user.type(descriptionInput, 'Task description');

    expect(descriptionInput.value).toBe('Task description');
  });

  test('updates due date field', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    const dueDateInput = screen.getByLabelText(/Due Date/i);
    await user.type(dueDateInput, '2025-01-20');

    expect(dueDateInput.value).toBe('2025-01-20');
  });

  test('updates priority when changed', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    const prioritySelect = screen.getByLabelText(/Priority/i);
    await user.selectOptions(prioritySelect, 'HIGH');

    expect(prioritySelect.value).toBe('HIGH');
  });

  test('submits form with valid data', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/Title/i), 'Test Task');
    await user.type(screen.getByLabelText(/Description/i), 'Test Description');
    await user.type(screen.getByLabelText(/Due Date/i), '2025-01-20');
    await user.selectOptions(screen.getByLabelText(/Priority/i), 'HIGH');

    await user.click(screen.getByRole('button', { name: /Create Task/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    const submittedData = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.title).toBe('Test Task');
    expect(submittedData.description).toBe('Test Description');
    expect(submittedData.priority).toBe('HIGH');
  });

  test('shows alert when title is missing', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/Due Date/i), '2025-01-20');
    await user.click(screen.getByRole('button', { name: /Create Task/i }));

    expect(window.alert).toHaveBeenCalledWith('Title and Due Date are required');
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('shows alert when due date is missing', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/Title/i), 'Test Task');
    await user.click(screen.getByRole('button', { name: /Create Task/i }));

    expect(window.alert).toHaveBeenCalledWith('Title and Due Date are required');
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('resets form after successful submission', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    const titleInput = screen.getByLabelText(/Title/i);
    const descriptionInput = screen.getByLabelText(/Description/i);
    const dueDateInput = screen.getByLabelText(/Due Date/i);
    const prioritySelect = screen.getByLabelText(/Priority/i);

    await user.type(titleInput, 'Test Task');
    await user.type(descriptionInput, 'Test Description');
    await user.type(dueDateInput, '2025-01-20');
    await user.selectOptions(prioritySelect, 'HIGH');

    await user.click(screen.getByRole('button', { name: /Create Task/i }));

    await waitFor(() => {
      expect(titleInput.value).toBe('');
      expect(descriptionInput.value).toBe('');
      expect(dueDateInput.value).toBe('');
      expect(prioritySelect.value).toBe('MEDIUM');
    });
  });

  test('shows Creating... text while submitting', async () => {
    const user = userEvent.setup();
    let resolveSubmit;
    const delayedSubmit = jest.fn(() => new Promise(resolve => {
      resolveSubmit = resolve;
    }));

    render(<TodoForm onSubmit={delayedSubmit} />);

    await user.type(screen.getByLabelText(/Title/i), 'Test Task');
    await user.type(screen.getByLabelText(/Due Date/i), '2025-01-20');

    const submitButton = screen.getByRole('button', { name: /Create Task/i });
    await user.click(submitButton);

    expect(screen.getByText(/Creating.../i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    resolveSubmit();

    await waitFor(() => {
      expect(screen.getByText(/Create Task/i)).toBeInTheDocument();
      expect(submitButton).not.toBeDisabled();
    });
  });

  test('handles submission error gracefully', async () => {
    const user = userEvent.setup();
    const mockErrorSubmit = jest.fn().mockRejectedValue(new Error('API Error'));
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<TodoForm onSubmit={mockErrorSubmit} />);

    await user.type(screen.getByLabelText(/Title/i), 'Test Task');
    await user.type(screen.getByLabelText(/Due Date/i), '2025-01-20');
    await user.click(screen.getByRole('button', { name: /Create Task/i }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Failed to create todo');
    });

    consoleErrorSpy.mockRestore();
  });

  test('submits with optional description empty', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/Title/i), 'Test Task');
    await user.type(screen.getByLabelText(/Due Date/i), '2025-01-20');
    await user.click(screen.getByRole('button', { name: /Create Task/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    const submittedData = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.description).toBe('');
  });

  test('allows all priority levels', async () => {
    const user = userEvent.setup();
    render(<TodoForm onSubmit={mockOnSubmit} />);

    const prioritySelect = screen.getByLabelText(/Priority/i);
    const options = Array.from(prioritySelect.options).map(opt => opt.value);

    expect(options).toContain('HIGH');
    expect(options).toContain('MEDIUM');
    expect(options).toContain('LOW');
    expect(options.length).toBe(3);
  });
});
