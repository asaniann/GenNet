'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { MainLayout } from '@/components/layout'
import { Card, CardBody, CardHeader, CardFooter } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Modal } from '@/components/ui/Modal'
import { SearchInput } from '@/components/ui/SearchInput'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Skeleton, SkeletonCard } from '@/components/ui/Skeleton'
import { DataTable, Column } from '@/components/ui/DataTable'
import { ProgressBar, CircularProgress } from '@/components/ui/ProgressBar'
import { Tabs, TabList, Tab, TabPanel } from '@/components/ui/Tabs'
import { useToast } from '@/components/ui/Toast'
import { Dropdown, DropdownItem, DropdownDivider } from '@/components/ui/Dropdown'
import { StatCard } from '@/components/ui/StatCard'
import { workflowApi } from '@/lib/api'

interface Workflow {
  id: string
  name: string
  description?: string
  type: string
  status: string
  progress: number
  network_id?: string
  network_name?: string
  created_at: string
  started_at?: string
  completed_at?: string
  duration?: number
  owner?: string
  config?: Record<string, any>
}

const workflowTypes = [
  { value: 'qualitative', label: 'Qualitative Analysis', icon: '🔬' },
  { value: 'hybrid', label: 'Hybrid Analysis', icon: '🧬' },
  { value: 'ml', label: 'ML-based Analysis', icon: '🤖' },
  { value: 'simulation', label: 'Network Simulation', icon: '📊' },
]

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  
  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [cancelModalOpen, setCancelModalOpen] = useState(false)
  const [workflowToCancel, setWorkflowToCancel] = useState<Workflow | null>(null)
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'qualitative',
    network_id: '',
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const { addToast } = useToast()

  const loadWorkflows = useCallback(async () => {
    try {
      setLoading(true)
      const response = await workflowApi.list()
      setWorkflows(response.data || [])
      setError(null)
    } catch (err: any) {
      // For demo, use mock data
      setWorkflows([
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
        {
          id: '2',
          name: 'p53 Pathway ML Prediction',
          description: 'Machine learning predictions for p53 pathway perturbations',
          type: 'ml',
          status: 'running',
          progress: 67,
          network_id: '2',
          network_name: 'p53 Signaling Pathway',
          created_at: '2025-12-30T14:30:00Z',
          started_at: '2025-12-30T14:31:00Z',
          owner: 'Sarah Smith',
        },
        {
          id: '3',
          name: 'Apoptosis Simulation',
          description: 'Time-series simulation of apoptosis network',
          type: 'simulation',
          status: 'pending',
          progress: 0,
          network_id: '3',
          network_name: 'Apoptosis Network v2',
          created_at: '2025-12-30T15:00:00Z',
          owner: 'Mike Johnson',
        },
        {
          id: '4',
          name: 'Wnt Hybrid Analysis',
          description: 'Combined qualitative and quantitative analysis',
          type: 'hybrid',
          status: 'failed',
          progress: 45,
          network_id: '4',
          network_name: 'Wnt Signaling',
          created_at: '2025-12-29T09:00:00Z',
          started_at: '2025-12-29T09:01:00Z',
          completed_at: '2025-12-29T09:23:00Z',
          duration: 1320,
          owner: 'Anna Lee',
        },
        {
          id: '5',
          name: 'Inflammatory Response Analysis',
          description: 'Qualitative analysis of NF-kB network',
          type: 'qualitative',
          status: 'completed',
          progress: 100,
          network_id: '5',
          network_name: 'Inflammatory Response',
          created_at: '2025-12-28T11:00:00Z',
          started_at: '2025-12-28T11:02:00Z',
          completed_at: '2025-12-28T11:45:00Z',
          duration: 2580,
          owner: 'John Doe',
        },
      ])
      setError(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadWorkflows()
    // Poll for updates every 10 seconds
    const interval = setInterval(loadWorkflows, 10000)
    return () => clearInterval(interval)
  }, [loadWorkflows])

  const getFilteredWorkflows = () => {
    return workflows
      .filter((workflow) => {
        const matchesSearch =
          workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          workflow.description?.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesType = !filterType || workflow.type === filterType
        const matchesTab =
          activeTab === 'all' ||
          (activeTab === 'running' && workflow.status === 'running') ||
          (activeTab === 'completed' && workflow.status === 'completed') ||
          (activeTab === 'failed' && workflow.status === 'failed')
        return matchesSearch && matchesType && matchesTab
      })
      .sort((a, b) => {
        if (sortBy === 'name') return a.name.localeCompare(b.name)
        if (sortBy === 'status') return a.status.localeCompare(b.status)
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
  }

  const filteredWorkflows = getFilteredWorkflows()

  const stats = {
    total: workflows.length,
    running: workflows.filter((w) => w.status === 'running').length,
    completed: workflows.filter((w) => w.status === 'completed').length,
    failed: workflows.filter((w) => w.status === 'failed').length,
  }

  const handleCreateWorkflow = async () => {
    const errors: Record<string, string> = {}
    if (!formData.name.trim()) {
      errors.name = 'Workflow name is required'
    }
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setSubmitting(true)
    try {
      await workflowApi.create(formData)
      addToast({
        type: 'success',
        title: 'Workflow Created',
        message: `"${formData.name}" has been created and queued.`,
      })
      setCreateModalOpen(false)
      setFormData({ name: '', description: '', type: 'qualitative', network_id: '' })
      loadWorkflows()
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to create workflow. Please try again.',
      })
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancelWorkflow = async () => {
    if (!workflowToCancel) return

    setSubmitting(true)
    try {
      await workflowApi.cancel(workflowToCancel.id)
      addToast({
        type: 'success',
        title: 'Workflow Cancelled',
        message: `"${workflowToCancel.name}" has been cancelled.`,
      })
      setCancelModalOpen(false)
      setWorkflowToCancel(null)
      loadWorkflows()
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to cancel workflow. Please try again.',
      })
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" dot>Completed</Badge>
      case 'running':
        return <Badge variant="primary" dot>Running</Badge>
      case 'pending':
        return <Badge variant="warning" dot>Pending</Badge>
      case 'failed':
        return <Badge variant="danger" dot>Failed</Badge>
      case 'cancelled':
        return <Badge variant="default" dot>Cancelled</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const getTypeBadge = (type: string) => {
    const typeConfig = workflowTypes.find((t) => t.value === type)
    return (
      <Badge variant="secondary">
        {typeConfig?.icon} {typeConfig?.label || type}
      </Badge>
    )
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-'
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  }

  const tableColumns: Column<Workflow>[] = [
    {
      key: 'name',
      header: 'Workflow',
      render: (workflow) => (
        <div className="min-w-[200px]">
          <Link href={`/workflows/${workflow.id}`} className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400">
            {workflow.name}
          </Link>
          {workflow.network_name && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Network: {workflow.network_name}
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (workflow) => getTypeBadge(workflow.type),
    },
    {
      key: 'status',
      header: 'Status',
      render: (workflow) => (
        <div className="flex items-center gap-2">
          {getStatusBadge(workflow.status)}
          {workflow.status === 'running' && (
            <span className="text-xs text-slate-500">{workflow.progress}%</span>
          )}
        </div>
      ),
    },
    {
      key: 'progress',
      header: 'Progress',
      render: (workflow) => (
        <div className="w-24">
          {workflow.status === 'running' ? (
            <ProgressBar value={workflow.progress} size="sm" animated />
          ) : workflow.status === 'completed' ? (
            <ProgressBar value={100} size="sm" color="success" />
          ) : workflow.status === 'failed' ? (
            <ProgressBar value={workflow.progress} size="sm" color="danger" />
          ) : (
            <ProgressBar value={0} size="sm" color="gray" />
          )}
        </div>
      ),
    },
    {
      key: 'duration',
      header: 'Duration',
      render: (workflow) => (
        <span className="text-sm text-slate-600 dark:text-slate-400">
          {workflow.status === 'running' && workflow.started_at
            ? 'Running...'
            : formatDuration(workflow.duration)}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      render: (workflow) => (
        <span className="text-sm text-slate-600 dark:text-slate-400">
          {new Date(workflow.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (workflow) => (
        <Dropdown
          align="right"
          trigger={
            <Button variant="ghost" size="icon-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </Button>
          }
        >
          <DropdownItem
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>}
          >
            View Details
          </DropdownItem>
          {workflow.status === 'completed' && (
            <DropdownItem
              icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
            >
              View Results
            </DropdownItem>
          )}
          <DropdownItem
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
          >
            Duplicate
          </DropdownItem>
          {workflow.status === 'running' && (
            <>
              <DropdownDivider />
              <DropdownItem
                variant="danger"
                icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>}
                onClick={() => {
                  setWorkflowToCancel(workflow)
                  setCancelModalOpen(true)
                }}
              >
                Cancel
              </DropdownItem>
            </>
          )}
        </Dropdown>
      ),
    },
  ]

  return (
    <MainLayout
      title="Workflows"
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Workflows' }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Workflows</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Run qualitative, hybrid, and ML-based analyses
            </p>
          </div>
          <Button onClick={() => setCreateModalOpen(true)} size="lg">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Workflow
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Workflows"
            value={stats.total}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            }
          />
          <StatCard
            title="Running"
            value={stats.running}
            change={stats.running > 0 ? 'Active' : undefined}
            trend={stats.running > 0 ? 'up' : undefined}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            iconColor="blue"
          />
          <StatCard
            title="Completed"
            value={stats.completed}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            iconColor="green"
          />
          <StatCard
            title="Failed"
            value={stats.failed}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            iconColor="red"
          />
        </div>

        {/* Tabs and Filters */}
        <Card padding="md">
          <Tabs value={activeTab} onChange={setActiveTab}>
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-4">
              <TabList>
                <Tab value="all">All ({workflows.length})</Tab>
                <Tab value="running">Running ({stats.running})</Tab>
                <Tab value="completed">Completed ({stats.completed})</Tab>
                <Tab value="failed">Failed ({stats.failed})</Tab>
              </TabList>
              <div className="flex flex-col sm:flex-row gap-3">
                <SearchInput
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onClear={() => setSearchQuery('')}
                  placeholder="Search workflows..."
                  className="w-full sm:w-64"
                />
                <Select
                  options={[
                    { value: '', label: 'All Types' },
                    ...workflowTypes.map((t) => ({ value: t.value, label: t.label })),
                  ]}
                  value={filterType}
                  onChange={setFilterType}
                  className="w-full sm:w-44"
                />
              </div>
            </div>
          </Tabs>
        </Card>

        {/* Running Workflows Highlight */}
        {stats.running > 0 && !loading && (
          <Card padding="md" className="border-l-4 border-l-blue-500 dark:border-l-blue-400">
            <h3 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-4">
              Running Workflows
            </h3>
            <div className="space-y-4">
              {workflows
                .filter((w) => w.status === 'running')
                .map((workflow) => (
                  <div key={workflow.id} className="flex items-center gap-4">
                    <div className="flex-shrink-0">
                      <CircularProgress value={workflow.progress} size={48} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <Link
                        href={`/workflows/${workflow.id}`}
                        className="font-medium text-slate-900 dark:text-slate-100 hover:text-blue-600 dark:hover:text-blue-400"
                      >
                        {workflow.name}
                      </Link>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        {workflow.network_name}
                      </p>
                    </div>
                    <div className="flex-shrink-0 text-sm text-slate-500 dark:text-slate-400">
                      Started {workflow.started_at && new Date(workflow.started_at).toLocaleTimeString()}
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setWorkflowToCancel(workflow)
                        setCancelModalOpen(true)
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                ))}
            </div>
          </Card>
        )}

        {/* Content */}
        {loading ? (
          <Card>
            <CardBody>
              <Skeleton variant="rounded" height={400} />
            </CardBody>
          </Card>
        ) : filteredWorkflows.length === 0 ? (
          <Card>
            <EmptyState
              icon={
                <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              }
              title={searchQuery ? 'No workflows found' : 'No workflows yet'}
              description={
                searchQuery
                  ? 'Try adjusting your search or filters'
                  : 'Create your first workflow to run network analyses'
              }
              action={
                !searchQuery && (
                  <Button onClick={() => setCreateModalOpen(true)}>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Create Workflow
                  </Button>
                )
              }
            />
          </Card>
        ) : (
          <Card>
            <DataTable
              data={filteredWorkflows}
              columns={tableColumns}
              keyExtractor={(workflow) => workflow.id}
              sortable
              pagination
              pageSize={10}
              onRowClick={(workflow) => window.location.href = `/workflows/${workflow.id}`}
            />
          </Card>
        )}
      </div>

      {/* Create Workflow Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false)
          setFormData({ name: '', description: '', type: 'qualitative', network_id: '' })
          setFormErrors({})
        }}
        title="Create New Workflow"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateWorkflow} loading={submitting}>
              Create Workflow
            </Button>
          </>
        }
      >
        <div className="space-y-6">
          <Input
            label="Workflow Name"
            placeholder="Enter workflow name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={formErrors.name}
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Description
            </label>
            <textarea
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              placeholder="Optional description"
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Analysis Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              {workflowTypes.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, type: type.value })}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    formData.type === type.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                  }`}
                >
                  <span className="text-2xl mb-2 block">{type.icon}</span>
                  <span className="font-medium text-slate-900 dark:text-slate-100 block">
                    {type.label}
                  </span>
                </button>
              ))}
            </div>
          </div>
          <Select
            label="Select Network"
            options={[
              { value: '', label: 'Choose a network...' },
              { value: '1', label: 'Cell Cycle Regulatory Network' },
              { value: '2', label: 'p53 Signaling Pathway' },
              { value: '3', label: 'Apoptosis Network v2' },
              { value: '4', label: 'Wnt Signaling' },
            ]}
            value={formData.network_id}
            onChange={(value) => setFormData({ ...formData, network_id: value })}
          />
        </div>
      </Modal>

      {/* Cancel Confirmation Modal */}
      <ConfirmDialog
        isOpen={cancelModalOpen}
        onClose={() => {
          setCancelModalOpen(false)
          setWorkflowToCancel(null)
        }}
        onConfirm={handleCancelWorkflow}
        title="Cancel Workflow"
        message={`Are you sure you want to cancel "${workflowToCancel?.name}"? This will stop the analysis and you may lose progress.`}
        confirmText="Cancel Workflow"
        variant="danger"
        loading={submitting}
      />
    </MainLayout>
  )
}

