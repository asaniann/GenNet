'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { MainLayout } from '@/components/layout'
import { Card, CardBody, CardHeader, CardFooter } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Select'
import { SearchInput } from '@/components/ui/SearchInput'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton, SkeletonCard } from '@/components/ui/Skeleton'
import { DataTable, Column } from '@/components/ui/DataTable'
import { Tabs, TabList, Tab, TabPanel } from '@/components/ui/Tabs'
import { useToast } from '@/components/ui/Toast'
import { Dropdown, DropdownItem, DropdownDivider } from '@/components/ui/Dropdown'
import { StatCard } from '@/components/ui/StatCard'
import { ProgressBar } from '@/components/ui/ProgressBar'

interface Analysis {
  id: string
  name: string
  type: string
  status: string
  workflow_id?: string
  workflow_name?: string
  network_id?: string
  network_name?: string
  created_at: string
  completed_at?: string
  attractors?: number
  steady_states?: number
  accuracy?: number
  results?: {
    summary?: string
    metrics?: Record<string, number>
    charts?: any[]
  }
}

const analysisTypes = [
  { value: 'qualitative', label: 'Qualitative', icon: '🔬' },
  { value: 'hybrid', label: 'Hybrid', icon: '🧬' },
  { value: 'ml', label: 'ML Prediction', icon: '🤖' },
  { value: 'simulation', label: 'Simulation', icon: '📊' },
]

export default function AnalysesPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid')
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('')
  const [sortBy, setSortBy] = useState('created_at')

  const { addToast } = useToast()

  const loadAnalyses = useCallback(async () => {
    try {
      setLoading(true)
      // For demo, use mock data
      setAnalyses([
        {
          id: '1',
          name: 'Cell Cycle Steady State Analysis',
          type: 'qualitative',
          status: 'completed',
          workflow_id: '1',
          workflow_name: 'Cell Cycle Qualitative Analysis',
          network_id: '1',
          network_name: 'Cell Cycle Regulatory Network',
          created_at: '2025-12-30T10:15:00Z',
          completed_at: '2025-12-30T10:15:00Z',
          attractors: 4,
          steady_states: 8,
          results: {
            summary: 'Found 4 attractors with 8 steady states representing different cell cycle phases',
            metrics: { attractors: 4, steady_states: 8, basin_sizes: 0.25 },
          },
        },
        {
          id: '2',
          name: 'p53 Pathway Perturbation Predictions',
          type: 'ml',
          status: 'completed',
          workflow_id: '2',
          workflow_name: 'p53 Pathway ML Prediction',
          network_id: '2',
          network_name: 'p53 Signaling Pathway',
          created_at: '2025-12-29T16:00:00Z',
          completed_at: '2025-12-29T16:00:00Z',
          accuracy: 94.5,
          results: {
            summary: 'ML model achieved 94.5% accuracy predicting perturbation effects',
            metrics: { accuracy: 94.5, precision: 92.3, recall: 96.1, f1_score: 94.2 },
          },
        },
        {
          id: '3',
          name: 'Wnt Dynamics Simulation',
          type: 'simulation',
          status: 'completed',
          workflow_id: '3',
          workflow_name: 'Wnt Hybrid Analysis',
          network_id: '4',
          network_name: 'Wnt Signaling',
          created_at: '2025-12-28T14:30:00Z',
          completed_at: '2025-12-28T14:30:00Z',
          results: {
            summary: 'Time-series simulation showing oscillatory behavior in canonical pathway',
            metrics: { time_steps: 1000, oscillation_period: 45, damping_factor: 0.02 },
          },
        },
        {
          id: '4',
          name: 'Inflammatory Response Attractors',
          type: 'qualitative',
          status: 'completed',
          workflow_id: '5',
          workflow_name: 'Inflammatory Response Analysis',
          network_id: '5',
          network_name: 'Inflammatory Response',
          created_at: '2025-12-28T11:45:00Z',
          completed_at: '2025-12-28T11:45:00Z',
          attractors: 6,
          steady_states: 12,
          results: {
            summary: 'Identified 6 attractors representing different inflammatory states',
            metrics: { attractors: 6, steady_states: 12, basin_sizes: 0.167 },
          },
        },
        {
          id: '5',
          name: 'Apoptosis Pathway Analysis',
          type: 'hybrid',
          status: 'processing',
          workflow_id: '6',
          workflow_name: 'Apoptosis Analysis',
          network_id: '3',
          network_name: 'Apoptosis Network v2',
          created_at: '2025-12-30T15:30:00Z',
        },
      ])
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load analyses')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAnalyses()
  }, [loadAnalyses])

  const filteredAnalyses = analyses
    .filter((analysis) => {
      const matchesSearch =
        analysis.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        analysis.network_name?.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesType = !filterType || analysis.type === filterType
      const matchesTab =
        activeTab === 'all' ||
        analysis.type === activeTab
      return matchesSearch && matchesType && matchesTab
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      if (sortBy === 'type') return a.type.localeCompare(b.type)
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })

  const stats = {
    total: analyses.length,
    qualitative: analyses.filter((a) => a.type === 'qualitative').length,
    ml: analyses.filter((a) => a.type === 'ml').length,
    simulation: analyses.filter((a) => a.type === 'simulation').length,
    hybrid: analyses.filter((a) => a.type === 'hybrid').length,
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" dot>Completed</Badge>
      case 'processing':
        return <Badge variant="primary" dot>Processing</Badge>
      case 'failed':
        return <Badge variant="danger" dot>Failed</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const getTypeBadge = (type: string) => {
    const typeConfig = analysisTypes.find((t) => t.value === type)
    const colorMap: Record<string, 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'default'> = {
      qualitative: 'primary',
      ml: 'success',
      simulation: 'secondary',
      hybrid: 'warning',
    }
    return (
      <Badge variant={colorMap[type] || 'default'}>
        {typeConfig?.icon} {typeConfig?.label || type}
      </Badge>
    )
  }

  const handleExport = (analysis: Analysis, format: string) => {
    addToast({
      type: 'info',
      title: 'Exporting...',
      message: `Exporting ${analysis.name} as ${format.toUpperCase()}`,
    })
    // Simulate export
    setTimeout(() => {
      addToast({
        type: 'success',
        title: 'Export Complete',
        message: `${analysis.name} exported successfully`,
      })
    }, 1500)
  }

  const tableColumns: Column<Analysis>[] = [
    {
      key: 'name',
      header: 'Analysis',
      render: (analysis) => (
        <div className="min-w-[200px]">
          <Link href={`/analyses/${analysis.id}`} className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400">
            {analysis.name}
          </Link>
          {analysis.network_name && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Network: {analysis.network_name}
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (analysis) => getTypeBadge(analysis.type),
    },
    {
      key: 'status',
      header: 'Status',
      render: (analysis) => getStatusBadge(analysis.status),
    },
    {
      key: 'metrics',
      header: 'Key Metrics',
      render: (analysis) => (
        <div className="text-sm text-slate-600 dark:text-slate-400">
          {analysis.attractors && (
            <span className="mr-3">Attractors: <strong>{analysis.attractors}</strong></span>
          )}
          {analysis.accuracy && (
            <span>Accuracy: <strong>{analysis.accuracy}%</strong></span>
          )}
          {!analysis.attractors && !analysis.accuracy && '-'}
        </div>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      render: (analysis) => (
        <span className="text-sm text-slate-600 dark:text-slate-400">
          {new Date(analysis.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (analysis) => (
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
          <DropdownDivider />
          <DropdownItem
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>}
            onClick={() => handleExport(analysis, 'json')}
          >
            Export JSON
          </DropdownItem>
          <DropdownItem
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>}
            onClick={() => handleExport(analysis, 'csv')}
          >
            Export CSV
          </DropdownItem>
          <DropdownItem
            icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>}
            onClick={() => handleExport(analysis, 'pdf')}
          >
            Export PDF
          </DropdownItem>
        </Dropdown>
      ),
    },
  ]

  return (
    <MainLayout
      title="Analyses"
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Analyses' }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Analysis Results</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              View and explore network analysis results
            </p>
          </div>
          <Button as="a" href="/workflows" variant="secondary" size="lg">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Run New Analysis
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            title="Total Analyses"
            value={stats.total}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
          />
          <StatCard
            title="Qualitative"
            value={stats.qualitative}
            icon={<span className="text-xl">🔬</span>}
          />
          <StatCard
            title="ML Predictions"
            value={stats.ml}
            icon={<span className="text-xl">🤖</span>}
          />
          <StatCard
            title="Simulations"
            value={stats.simulation}
            icon={<span className="text-xl">📊</span>}
          />
          <StatCard
            title="Hybrid"
            value={stats.hybrid}
            icon={<span className="text-xl">🧬</span>}
          />
        </div>

        {/* Filters */}
        <Card padding="md">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <SearchInput
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onClear={() => setSearchQuery('')}
                placeholder="Search analyses..."
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              <Select
                options={[
                  { value: '', label: 'All Types' },
                  ...analysisTypes.map((t) => ({ value: t.value, label: `${t.icon} ${t.label}` })),
                ]}
                value={filterType}
                onChange={setFilterType}
                className="w-full sm:w-44"
              />
              <Select
                options={[
                  { value: 'created_at', label: 'Newest First' },
                  { value: 'name', label: 'Name (A-Z)' },
                  { value: 'type', label: 'Type' },
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
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
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
        ) : filteredAnalyses.length === 0 ? (
          <Card>
            <EmptyState
              icon={
                <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
              title={searchQuery ? 'No analyses found' : 'No analyses yet'}
              description={
                searchQuery
                  ? 'Try adjusting your search or filters'
                  : 'Run a workflow to generate analysis results'
              }
              action={
                !searchQuery && (
                  <Button as="a" href="/workflows">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Go to Workflows
                  </Button>
                )
              }
            />
          </Card>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredAnalyses.map((analysis) => (
              <Card key={analysis.id} hover>
                <CardBody>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getTypeBadge(analysis.type)}
                      {getStatusBadge(analysis.status)}
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
                      <DropdownItem onClick={() => handleExport(analysis, 'json')}>Export JSON</DropdownItem>
                      <DropdownItem onClick={() => handleExport(analysis, 'csv')}>Export CSV</DropdownItem>
                      <DropdownItem onClick={() => handleExport(analysis, 'pdf')}>Export PDF</DropdownItem>
                    </Dropdown>
                  </div>
                  <Link href={`/analyses/${analysis.id}`}>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      {analysis.name}
                    </h3>
                  </Link>
                  {analysis.network_name && (
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                      Network: {analysis.network_name}
                    </p>
                  )}
                  {analysis.results?.summary && (
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-2">
                      {analysis.results.summary}
                    </p>
                  )}
                  
                  {/* Metrics */}
                  {analysis.status === 'completed' && (
                    <div className="space-y-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                      {analysis.attractors !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-500 dark:text-slate-400">Attractors Found</span>
                          <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">{analysis.attractors}</span>
                        </div>
                      )}
                      {analysis.steady_states !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-500 dark:text-slate-400">Steady States</span>
                          <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">{analysis.steady_states}</span>
                        </div>
                      )}
                      {analysis.accuracy !== undefined && (
                        <div>
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm text-slate-500 dark:text-slate-400">Model Accuracy</span>
                            <span className="text-sm font-semibold text-green-600">{analysis.accuracy}%</span>
                          </div>
                          <ProgressBar value={analysis.accuracy} size="sm" color="green" />
                        </div>
                      )}
                    </div>
                  )}
                  {analysis.status === 'processing' && (
                    <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
                      <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Processing analysis...
                      </div>
                    </div>
                  )}
                </CardBody>
                <CardFooter className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {new Date(analysis.created_at).toLocaleDateString()}
                  </span>
                  <Button variant="ghost" size="sm" as="a" href={`/analyses/${analysis.id}`}>
                    View Details
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
              data={filteredAnalyses}
              columns={tableColumns}
              keyExtractor={(analysis) => analysis.id}
              sortable
              pagination
              pageSize={10}
              onRowClick={(analysis) => window.location.href = `/analyses/${analysis.id}`}
            />
          </Card>
        )}
      </div>
    </MainLayout>
  )
}

