import { create } from 'zustand'

export interface Workflow {
  id: string
  name: string
  description?: string
  type: 'qualitative' | 'hybrid' | 'ml' | 'simulation'
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  network_id?: string
  network_name?: string
  owner?: string
  config?: Record<string, any>
  created_at: string
  started_at?: string
  completed_at?: string
  duration?: number
  error?: string
  results?: {
    summary?: string
    metrics?: Record<string, number>
    analysis_id?: string
  }
}

interface WorkflowState {
  // State
  workflows: Workflow[]
  currentWorkflow: Workflow | null
  runningWorkflows: Workflow[]
  isLoading: boolean
  error: string | null
  filters: {
    search: string
    type: string
    status: string
    sortBy: string
  }
  
  // Actions
  setWorkflows: (workflows: Workflow[]) => void
  setCurrentWorkflow: (workflow: Workflow | null) => void
  addWorkflow: (workflow: Workflow) => void
  updateWorkflow: (id: string, updates: Partial<Workflow>) => void
  deleteWorkflow: (id: string) => void
  
  // Workflow operations
  startWorkflow: (id: string) => Promise<void>
  cancelWorkflow: (id: string) => Promise<void>
  retryWorkflow: (id: string) => Promise<void>
  
  // Filter operations
  setFilters: (filters: Partial<WorkflowState['filters']>) => void
  clearFilters: () => void
  
  // Async operations
  fetchWorkflows: () => Promise<void>
  fetchWorkflow: (id: string) => Promise<void>
  createWorkflow: (data: Partial<Workflow>) => Promise<Workflow>
  
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

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // Initial state
  workflows: [],
  currentWorkflow: null,
  runningWorkflows: [],
  isLoading: false,
  error: null,
  filters: defaultFilters,

  // Actions
  setWorkflows: (workflows) => set({ 
    workflows,
    runningWorkflows: workflows.filter((w) => w.status === 'running'),
  }),
  
  setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),
  
  addWorkflow: (workflow) => set((state) => ({
    workflows: [workflow, ...state.workflows],
    runningWorkflows: workflow.status === 'running'
      ? [workflow, ...state.runningWorkflows]
      : state.runningWorkflows,
  })),
  
  updateWorkflow: (id, updates) => set((state) => {
    const updatedWorkflows = state.workflows.map((w) =>
      w.id === id ? { ...w, ...updates } : w
    )
    
    return {
      workflows: updatedWorkflows,
      runningWorkflows: updatedWorkflows.filter((w) => w.status === 'running'),
      currentWorkflow: state.currentWorkflow?.id === id
        ? { ...state.currentWorkflow, ...updates }
        : state.currentWorkflow,
    }
  }),
  
  deleteWorkflow: (id) => set((state) => ({
    workflows: state.workflows.filter((w) => w.id !== id),
    runningWorkflows: state.runningWorkflows.filter((w) => w.id !== id),
    currentWorkflow: state.currentWorkflow?.id === id ? null : state.currentWorkflow,
  })),
  
  // Workflow operations
  startWorkflow: async (id) => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 300))
      
      get().updateWorkflow(id, {
        status: 'running',
        progress: 0,
        started_at: new Date().toISOString(),
      })
      
      set({ isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to start workflow', isLoading: false })
      throw error
    }
  },
  
  cancelWorkflow: async (id) => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 300))
      
      const workflow = get().workflows.find((w) => w.id === id)
      const startedAt = workflow?.started_at ? new Date(workflow.started_at) : new Date()
      const duration = Math.floor((Date.now() - startedAt.getTime()) / 1000)
      
      get().updateWorkflow(id, {
        status: 'cancelled',
        completed_at: new Date().toISOString(),
        duration,
      })
      
      set({ isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to cancel workflow', isLoading: false })
      throw error
    }
  },
  
  retryWorkflow: async (id) => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 300))
      
      get().updateWorkflow(id, {
        status: 'pending',
        progress: 0,
        error: undefined,
        started_at: undefined,
        completed_at: undefined,
        duration: undefined,
      })
      
      set({ isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to retry workflow', isLoading: false })
      throw error
    }
  },
  
  // Filter operations
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
  })),
  
  clearFilters: () => set({ filters: defaultFilters }),
  
  // Async operations
  fetchWorkflows: async () => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call - replace with actual API
      await new Promise((resolve) => setTimeout(resolve, 500))
      
      // Mock data
      const mockWorkflows: Workflow[] = [
        {
          id: '1',
          name: 'Cell Cycle Qualitative Analysis',
          description: 'Steady state analysis of cell cycle network',
          type: 'qualitative',
          status: 'completed',
          progress: 100,
          network_id: '1',
          network_name: 'Cell Cycle Regulatory Network',
          created_at: '2025-12-30T10:00:00Z',
          started_at: '2025-12-30T10:01:00Z',
          completed_at: '2025-12-30T10:15:00Z',
          duration: 840,
          owner: 'John Doe',
        },
      ]
      
      set({ 
        workflows: mockWorkflows,
        runningWorkflows: mockWorkflows.filter((w) => w.status === 'running'),
        isLoading: false,
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch workflows', isLoading: false })
    }
  },
  
  fetchWorkflow: async (id) => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 300))
      
      const workflow = get().workflows.find((w) => w.id === id) || null
      set({ currentWorkflow: workflow, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch workflow', isLoading: false })
    }
  },
  
  createWorkflow: async (data) => {
    set({ isLoading: true, error: null })
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500))
      
      const workflow: Workflow = {
        id: Date.now().toString(),
        name: data.name || 'Untitled Workflow',
        description: data.description,
        type: data.type || 'qualitative',
        status: 'pending',
        progress: 0,
        network_id: data.network_id,
        network_name: data.network_name,
        owner: data.owner,
        config: data.config,
        created_at: new Date().toISOString(),
      }
      
      get().addWorkflow(workflow)
      set({ isLoading: false })
      return workflow
    } catch (error: any) {
      set({ error: error.message || 'Failed to create workflow', isLoading: false })
      throw error
    }
  },
  
  // Utilities
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}))
