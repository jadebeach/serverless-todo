import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

// Mock Amplify
jest.mock('aws-amplify', () => ({
  Amplify: {
    configure: jest.fn()
  }
}));

jest.mock('aws-amplify/auth', () => ({
  fetchAuthSession: jest.fn()
}));

jest.mock('@aws-amplify/ui-react', () => ({
  Authenticator: ({ children }) => children({
    signOut: jest.fn(),
    user: {
      signInDetails: { loginId: 'test@example.com' }
    }
  }),
  __esModule: true
}));

// Mock fetch
global.fetch = jest.fn();

const mockAuthSession = {
  tokens: {
    idToken: {
      toString: () => 'mock-id-token'
    }
  }
};

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    const { fetchAuthSession } = require('aws-amplify/auth');
    fetchAuthSession.mockResolvedValue(mockAuthSession);
  });

  test('renders app header', () => {
    render(<App />);
    expect(screen.getByText(/Serverless Todo App/i)).toBeInTheDocument();
  });

  test('renders user email', () => {
    render(<App />);
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  test('renders sign out button', () => {
    render(<App />);
    expect(screen.getByText(/Sign Out/i)).toBeInTheDocument();
  });

  test('displays error message when API fails', async () => {
    global.fetch.mockRejectedValueOnce(new Error('API Error'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/API Error/i)).toBeInTheDocument();
    });
  });

  test('displays loading state initially', () => {
    global.fetch.mockImplementationOnce(() => new Promise(() => {})); // Never resolves

    render(<App />);

    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });
});
