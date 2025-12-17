/**
 * Tests for API client
 */

// Mock axios - everything must be defined inside the factory
jest.mock('axios', () => {
  const mockInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: {
        use: jest.fn(),
      },
      response: {
        use: jest.fn(),
      },
    },
  };
  
  // Store reference globally so we can access it
  (global as any).__MOCK_AXIOS_INSTANCE__ = mockInstance;
  
  return {
    __esModule: true,
    default: {
      create: jest.fn(() => mockInstance),
    },
  };
});

// Now import the API module after mocking
import { networkApi, workflowApi, authApi } from '../lib/api';

// Get the mock instance from global
const getMockInstance = () => {
  return (global as any).__MOCK_AXIOS_INSTANCE__ || {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
};

describe('API Client', () => {
  let mockInstance: any;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('auth_token', 'test-token');
    mockInstance = getMockInstance();
  });

  afterEach(() => {
    localStorage.removeItem('auth_token');
  });

  describe('networkApi', () => {
    it('should list networks', async () => {
      const mockNetworks = [{ id: '1', name: 'Network 1' }];
      (mockInstance.get as jest.Mock).mockResolvedValue({ data: mockNetworks });

      const result = await networkApi.list();
      expect(result.data).toEqual(mockNetworks);
      expect(mockInstance.get).toHaveBeenCalledWith('/api/v1/networks');
    });

    it('should create a network', async () => {
      const mockNetwork = { id: '1', name: 'New Network' };
      (mockInstance.post as jest.Mock).mockResolvedValue({ data: mockNetwork });

      const result = await networkApi.create(mockNetwork);
      expect(result.data).toEqual(mockNetwork);
      expect(mockInstance.post).toHaveBeenCalledWith('/api/v1/networks', mockNetwork);
    });
  });

  describe('workflowApi', () => {
    it('should list workflows', async () => {
      const mockWorkflows = [{ id: '1', name: 'Workflow 1' }];
      (mockInstance.get as jest.Mock).mockResolvedValue({ data: mockWorkflows });

      const result = await workflowApi.list();
      expect(result.data).toEqual(mockWorkflows);
      expect(mockInstance.get).toHaveBeenCalledWith('/api/v1/workflows');
    });
  });

  describe('authApi', () => {
    it('should login', async () => {
      const mockToken = { access_token: 'token', token_type: 'bearer' };
      (mockInstance.post as jest.Mock).mockResolvedValue({ data: mockToken });

      const result = await authApi.login('user', 'pass');
      expect(result.data).toEqual(mockToken);
      expect(mockInstance.post).toHaveBeenCalledWith(
        '/api/v1/auth/token',
        expect.any(URLSearchParams),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })
      );
    });
  });
});
