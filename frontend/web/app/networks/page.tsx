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
import { useToast } from '@/components/ui/Toast'
import { Dropdown, DropdownItem, DropdownDivider } from '@/components/ui/Dropdown'
import { networkApi } from '@/lib/api'

interface Network {
  id: string
  name: string
  description?: string
  nodes: number
  edges: number
  type: string
  status: string
  created_at: string
  updated_at: string
  owner?: string
}

export default function NetworksPage() {
  const [networks, setNetworks] = useState<Network[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  
  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [networkToDelete, setNetworkToDelete] = useState<Network | null>(null)
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'grn',
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const { addToast } = useToast()

  const loadNetworks = useCallback(async () => {
    try {
      setLoading(true)
      const response = await networkApi.list()
      setNetworks(response.data || [])
      setError(null)
    } catch (err: any) {
      // For demo, use mock data
      setNetworks([
        {
          id: '1',
          name: 'Cell Cycle Regulatory Network',
          description: 'Complete cell cycle GRN with checkpoint controls',
          nodes: 45,
          edges: 156,
          type: 'grn',
          status: 'active',
          created_at: '2025-12-28T10:30:00Z',
          updated_at: '2025-12-30T14:20:00Z',
          owner: 'John Doe',
        },
        {
          id: '2',
          name: 'p53 Signaling Pathway',
          description: 'Tumor suppressor p53 pathway network',
          nodes: 32,
          edges: 89,
          type: 'pathway',
          status: 'active',
          created_at: '2025-12-25T08:15:00Z',
          updated_at: '2025-12-29T11:45:00Z',
          owner: 'Sarah Smith',
        },
        {
          id: '3',
          name: 'Apoptosis Network v2',
          description: 'Programmed cell death regulatory network',
          nodes: 28,
          edges: 67,
          type: 'grn',
          status: 'draft',
          created_at: '2025-12-20T16:00:00Z',
          updated_at: '2025-12-20T16:00:00Z',
          owner: 'Mike Johnson',
        },
        {
          id: '4',
          name: 'Wnt Signaling',
          description: 'Canonical and non-canonical Wnt pathways',
          nodes: 56,
          edges: 203,
          type: 'pathway',
          status: 'active',
          created_at: '2025-12-15T09:30:00Z',
          updated_at: '2025-12-28T15:30:00Z',
          owner: 'Anna Lee',
        },
        {
          id: '5',
          name: 'Inflammatory Response',
          description: 'NF-kB mediated inflammatory response network',
          nodes: 41,
          edges: 134,
          type: 'grn',
          status: 'archived',
          created_at: '2025-11-10T12:00:00Z',
          updated_at: '2025-12-01T10:00:00Z',
          owner: 'John Doe',
        },
      ])
      setError(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadNetworks()
  }, [loadNetworks])

  const filteredNetworks = networks
    .filter((network) => {
      const matchesSearch =
        network.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        network.description?.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesType = !filterType || network.type === filterType
      return matchesSearch && matchesType
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      if (sortBy === 'nodes') return b.nodes - a.nodes
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })

  const handleCreateNetwork = async () => {
    const errors: Record<string, string> = {}
    if (!formData.name.trim()) {
      errors.name = 'Network name is required'
    }
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setSubmitting(true)
    try {
      await networkApi.create(formData)
      addToast({
        type: 'success',
        title: 'Network Created',
        message: `"${formData.name}" has been created successfully.`,
      })
      setCreateModalOpen(false)
      setFormData({ name: '', description: '', type: 'grn' })
      loadNetworks()
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to create network. Please try again.',
      })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteNetwork = async () => {
    if (!networkToDelete) return

    setSubmitting(true)
    try {
      await networkApi.delete(networkToDelete.id)
      addToast({
        type: 'success',
        title: 'Network Deleted',
        message: `"${networkToDelete.name}" has been deleted.`,
      })
      setDeleteModalOpen(false)
      setNetworkToDelete(null)
      loadNetworks()
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to delete network. Please try again.',
      })
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="success" dot>Active</Badge>
      case 'draft':
        return <Badge variant="warning" dot>Draft</Badge>
      case 'archived':
        return <Badge variant="default" dot>Archived</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'grn':
        return <Badge variant="primary">GRN</Badge>
      case 'pathway':
        return <Badge variant="secondary">Pathway</Badge>
      default:
        return <Badge>{type}</Badge>
    }
  }

  const tableColumns: Column<Network>[] = [
    {
      key: 'name',
      header: 'Name',
      render: (network) => (
        <div>
          <Link href={`/networks/${network.id}`} className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400">
            {network.name}
          </Link>
          {network.description && (
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-xs">{network.description}</p>
          )}
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (network) => getTypeBadge(network.type),
    },
    {
      key: 'nodes',
      header: 'Nodes',
      sortable: true,
    },
    {
      key: 'edges',
      header: 'Edges',
      sortable: true,
    },
    {
      key: 'status',
      header: 'Status',
      render: (network) => getStatusBadge(network.status),
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      render: (network) => new Date(network.created_at).toLocaleDateString(),
    },
    {
      key: 'actions',
      header: '',
      render: (network) => (
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
            View
          </DropdownItem>
          <DropdownItem
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>}
          >
            Edit
          </DropdownItem>
          <DropdownItem
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
          >
            Duplicate
          </DropdownItem>
          <DropdownDivider />
          <DropdownItem
            variant="danger"
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>}
            onClick={() => {
              setNetworkToDelete(network)
              setDeleteModalOpen(true)
            }}
          >
            Delete
          </DropdownItem>
        </Dropdown>
      ),
    },
  ]

  return (
    <MainLayout
      title="Networks"
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Networks' }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Networks</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Create, edit, and manage Gene Regulatory Networks
            </p>
          </div>
          <Button onClick={() => setCreateModalOpen(true)} size="lg">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Network
          </Button>
        </div>

        {/* Filters */}
        <Card padding="md">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <SearchInput
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onClear={() => setSearchQuery('')}
                placeholder="Search networks..."
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              <Select
                options={[
                  { value: '', label: 'All Types' },
                  { value: 'grn', label: 'GRN' },
                  { value: 'pathway', label: 'Pathway' },
                ]}
                value={filterType}
                onChange={setFilterType}
                className="w-full sm:w-40"
              />
              <Select
                options={[
                  { value: 'created_at', label: 'Newest First' },
                  { value: 'name', label: 'Name (A-Z)' },
                  { value: 'nodes', label: 'Most Nodes' },
                ]}
                value={sortBy}
                onChange={setSortBy}
                className="w-full sm:w-40"
              />
              <div className="flex border border-slate-300 dark:border-slate-600 rounded-lg overflow-hidden">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2.5 ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'}`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('table')}
                  className={`p-2.5 ${viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'}`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </Card>

        {/* Content */}
        {loading ? (
          viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <Card>
              <CardBody>
                <Skeleton variant="rounded" height={300} />
              </CardBody>
            </Card>
          )
        ) : filteredNetworks.length === 0 ? (
          <Card>
            <EmptyState
              icon={
                <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
              title={searchQuery ? 'No networks found' : 'No networks yet'}
              description={
                searchQuery
                  ? 'Try adjusting your search or filters'
                  : 'Create your first Gene Regulatory Network to get started'
              }
              action={
                !searchQuery && (
                  <Button onClick={() => setCreateModalOpen(true)}>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Create Network
                  </Button>
                )
              }
            />
          </Card>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredNetworks.map((network) => (
              <Card key={network.id} hover>
                <CardBody>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getTypeBadge(network.type)}
                      {getStatusBadge(network.status)}
                    </div>
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
                      <DropdownItem>Edit</DropdownItem>
                      <DropdownItem>Duplicate</DropdownItem>
                      <DropdownDivider />
                      <DropdownItem
                        variant="danger"
                        onClick={() => {
                          setNetworkToDelete(network)
                          setDeleteModalOpen(true)
                        }}
                      >
                        Delete
                      </DropdownItem>
                    </Dropdown>
                  </div>
                  <Link href={`/networks/${network.id}`}>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      {network.name}
                    </h3>
                  </Link>
                  {network.description && (
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 line-clamp-2">
                      {network.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="3" strokeWidth={2} />
                      </svg>
                      {network.nodes} nodes
                    </div>
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      {network.edges} edges
                    </div>
                  </div>
                </CardBody>
                <CardFooter className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    Updated {new Date(network.updated_at).toLocaleDateString()}
                  </span>
                  <Button variant="ghost" size="sm" as="a" href={`/networks/${network.id}`}>
                    Open
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <DataTable
              data={filteredNetworks}
              columns={tableColumns}
              keyExtractor={(network) => network.id}
              sortable
              pagination
              pageSize={10}
              onRowClick={(network) => window.location.href = `/networks/${network.id}`}
            />
          </Card>
        )}
      </div>

      {/* Create Network Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false)
          setFormData({ name: '', description: '', type: 'grn' })
          setFormErrors({})
        }}
        title="Create New Network"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateNetwork} loading={submitting}>
              Create Network
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Network Name"
            placeholder="Enter network name"
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
          <Select
            label="Network Type"
            options={[
              { value: 'grn', label: 'Gene Regulatory Network (GRN)' },
              { value: 'pathway', label: 'Signaling Pathway' },
            ]}
            value={formData.type}
            onChange={(value) => setFormData({ ...formData, type: value })}
          />
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmDialog
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false)
          setNetworkToDelete(null)
        }}
        onConfirm={handleDeleteNetwork}
        title="Delete Network"
        message={`Are you sure you want to delete "${networkToDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        loading={submitting}
      />
    </MainLayout>
  )
}

