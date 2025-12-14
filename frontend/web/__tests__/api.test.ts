/**
 * Tests for API client
 */

import { networkApi, workflowApi, authApi } from '../lib/api';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('auth_token', 'test-token');
  });

  afterEach(() => {
    localStorage.removeItem('auth_token');
  });

  describe('networkApi', () => {
    it('should list networks', async () => {
      const mockNetworks = [{ id: '1', name: 'Network 1' }];
      mockedAxios.create.mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: mockNetworks }),
      } as any);

      const result = await networkApi.list();
      expect(result.data).toEqual(mockNetworks);
    });

    it('should create a network', async () => {
      const mockNetwork = { id: '1', name: 'New Network' };
      mockedAxios.create.mockReturnValue({
        post: jest.fn().mockResolvedValue({ data: mockNetwork }),
      } as any);

      const result = await networkApi.create(mockNetwork);
      expect(result.data).toEqual(mockNetwork);
    });
  });

  describe('workflowApi', () => {
    it('should list workflows', async () => {
      const mockWorkflows = [{ id: '1', name: 'Workflow 1' }];
      mockedAxios.create.mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: mockWorkflows }),
      } as any);

      const result = await workflowApi.list();
      expect(result.data).toEqual(mockWorkflows);
    });
  });

  describe('authApi', () => {
    it('should login', async () => {
      const mockToken = { access_token: 'token', token_type: 'bearer' };
      mockedAxios.create.mockReturnValue({
        post: jest.fn().mockResolvedValue({ data: mockToken }),
      } as any);

      const result = await authApi.login('user', 'pass');
      expect(result.data).toEqual(mockToken);
    });
  });
});

