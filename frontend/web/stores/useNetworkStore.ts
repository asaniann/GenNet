import { create } from 'zustand'
import { Node, Edge } from 'react-flow-renderer'

export interface Network {
  id: string
  name: string
  description?: string
  type: 'grn' | 'pathway'
  status: 'active' | 'draft' | 'archived'
  nodes: Node[]
  edges: Edge[]
  owner?: string
  created_at: string
  updated_at: string
  tags?: string[]
  metadata?: Record<string, any>
}

interface NetworkState {
  // State
  networks: Network[]
  currentNetwork: Network | null
  isLoading: boolean
  error: string | null
  filters: {
    search: string
    type: string
    status: string
    sortBy: string
  }
  
  // Actions
  setNetworks: (networks: Network[]) => void
  setCurrentNetwork: (network: Network | null) => void
  addNetwork: (network: Network) => void
  updateNetwork: (id: string, updates: Partial<Network>) => void
  deleteNetwork: (id: string) => void
  
  // Node/Edge operations
  addNode: (networkId: string, node: Node) => void
  updateNode: (networkId: string, nodeId: string, updates: Partial<Node>) => void
  deleteNode: (networkId: string, nodeId: string) => void
  addEdge: (networkId: string, edge: Edge) => void
  updateEdge: (networkId: string, edgeId: string, updates: Partial<Edge>) => void
  deleteEdge: (networkId: string, edgeId: string) => void
  
  // Filter operations
  setFilters: (filters: Partial<NetworkState['filters']>) => void
  clearFilters: () => void
  
  // Async operations
  fetchNetworks: () => Promise<void>
  fetchNetwork: (id: string) => Promise<void>
  saveNetwork: (network: Partial<Network>) => Promise<Network>
  
  // Utilities
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

const defaultFilters = {
  search: '',
  type: '',
  status: '',
  sortBy: 'created_at',
}

export const useNetworkStore = create<NetworkState>((set, get) => ({
  // Initial state
  networks: [],
  currentNetwork: null,
  isLoading: false,
  error: null,
  filters: defaultFilters,

  // Actions
  setNetworks: (networks) => set({ networks }),
  
  setCurrentNetwork: (network) => set({ currentNetwork: network }),
  
  addNetwork: (network) => set((state) => ({
    networks: [network, ...state.networks],
  })),
  
  updateNetwork: (id, updates) => set((state) => ({
    networks: state.networks.map((n) =>
      n.id === id ? { ...n, ...updates, updated_at: new Date().toISOString() } : n
    ),
    currentNetwork: state.currentNetwork?.id === id
      ? { ...state.currentNetwork, ...updates, updated_at: new Date().toISOString() }
      : state.currentNetwork,
  })),
  
  deleteNetwork: (id) => set((state) => ({
    networks: state.networks.filter((n) => n.id !== id),
    currentNetwork: state.currentNetwork?.id === id ? null : state.currentNetwork,
  })),
  
  // Node operations
  addNode: (networkId, node) => set((state) => {
    const updateFn = (network: Network): Network => ({
      ...network,
      nodes: [...network.nodes, node],
      updated_at: new Date().toISOString(),
    })
    
    return {
      networks: state.networks.map((n) => n.id === networkId ? updateFn(n) : n),
      currentNetwork: state.currentNetwork?.id === networkId
        ? updateFn(state.currentNetwork)
        : state.currentNetwork,
    }
  }),
  
  updateNode: (networkId, nodeId, updates) => set((state) => {
    const updateFn = (network: Network): Network => ({
      ...network,
      nodes: network.nodes.map((n) =>
        n.id === nodeId ? { ...n, ...updates } : n
      ),
      updated_at: new Date().toISOString(),
    })
    
    return {
      networks: state.networks.map((n) => n.id === networkId ? updateFn(n) : n),
      currentNetwork: state.currentNetwork?.id === networkId
        ? updateFn(state.currentNetwork)
        : state.currentNetwork,
    }
  }),
  
  deleteNode: (networkId, nodeId) => set((state) => {
    const updateFn = (network: Network): Network => ({
      ...network,
      nodes: network.nodes.filter((n) => n.id !== nodeId),
      edges: network.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      updated_at: new Date().toISOString(),
    })
    
    return {
      networks: state.networks.map((n) => n.id === networkId ? updateFn(n) : n),
      currentNetwork: state.currentNetwork?.id === networkId
        ? updateFn(state.currentNetwork)
        : state.currentNetwork,
    }
  }),
  
  addEdge: (networkId, edge) => set((state) => {
    const updateFn = (network: Network): Network => ({
      ...network,
      edges: [...network.edges, edge],
      updated_at: new Date().toISOString(),
    })
    
    return {
      networks: state.networks.map((n) => n.id === networkId ? updateFn(n) : n),
      currentNetwork: state.currentNetwork?.id === networkId
        ? updateFn(state.currentNetwork)
        : state.currentNetwork,
    }
  }),
  
  updateEdge: (networkId, edgeId, updates) => set((state) => {
    const updateFn = (network: Network): Network => ({
      ...network,
      edges: network.edges.map((e) =>
        e.id === edgeId ? { ...e, ...updates } : e
      ),
      updated_at: new Date().toISOString(),
    })
    
    return {
      networks: state.networks.map((n) => n.id === networkId ? updateFn(n) : n),
      currentNetwork: state.currentNetwork?.id === networkId
        ? updateFn(state.currentNetwork)
        : state.currentNetwork,
    }
  }),
  
  deleteEdge: (networkId, edgeId) => set((state) => {
    const updateFn = (network: Network): Network => ({
      ...network,
      edges: network.edges.filter((e) => e.id !== edgeId),
      updated_at: new Date().toISOString(),
    })
    
    return {
      networks: state.networks.map((n) => n.id === networkId ? updateFn(n) : n),
      currentNetwork: state.currentNetwork?.id === networkId
        ? updateFn(state.currentNetwork)
        : state.currentNetwork,
    }
  }),
  
  // Filter operations
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
  })),
  
  clearFilters: () => set({ filters: defaultFilters }),
  
  // Async operations
  fetchNetworks: async () => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call - replace with actual API
      await new Promise((resolve) => setTimeout(resolve, 500))
      
      // Mock data
      const mockNetworks: Network[] = [
        {
          id: '1',
          name: 'Cell Cycle Regulatory Network',
          description: 'Complete cell cycle GRN with checkpoint controls',
          type: 'grn',
          status: 'active',
          nodes: [],
          edges: [],
          owner: 'John Doe',
          created_at: '2025-12-28T10:30:00Z',
          updated_at: '2025-12-30T14:20:00Z',
        },
      ]
      
      set({ networks: mockNetworks, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch networks', isLoading: false })
    }
  },
  
  fetchNetwork: async (id) => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 300))
      
      const network = get().networks.find((n) => n.id === id) || null
      set({ currentNetwork: network, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch network', isLoading: false })
    }
  },
  
  saveNetwork: async (networkData) => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500))
      
      const isNew = !networkData.id
      const network: Network = {
        id: networkData.id || Date.now().toString(),
        name: networkData.name || 'Untitled Network',
        description: networkData.description,
        type: networkData.type || 'grn',
        status: networkData.status || 'draft',
        nodes: networkData.nodes || [],
        edges: networkData.edges || [],
        owner: networkData.owner,
        created_at: isNew ? new Date().toISOString() : (networkData.created_at || new Date().toISOString()),
        updated_at: new Date().toISOString(),
        tags: networkData.tags,
        metadata: networkData.metadata,
      }
      
      if (isNew) {
        get().addNetwork(network)
      } else {
        get().updateNetwork(network.id, network)
      }
      
      set({ isLoading: false })
      return network
    } catch (error: any) {
      set({ error: error.message || 'Failed to save network', isLoading: false })
      throw error
    }
  },
  
  // Utilities
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}))
