'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { MainLayout } from '@/components/layout'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { StatCard } from '@/components/ui/StatCard'
import { ProgressBar, CircularProgress } from '@/components/ui/ProgressBar'
import { Avatar, AvatarGroup } from '@/components/ui/Avatar'
import { Skeleton, SkeletonCard } from '@/components/ui/Skeleton'

interface DashboardStats {
  networks: number
  workflows: number
  analyses: number
  computeUsage: number
}

interface RecentActivity {
  id: string
  type: 'network' | 'workflow' | 'analysis'
  action: string
  name: string
  time: string
  user?: string
}

interface RunningWorkflow {
  id: string
  name: string
  progress: number
  status: 'running' | 'queued'
  startedAt: string
}

export default function Home() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [runningWorkflows, setRunningWorkflows] = useState<RunningWorkflow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate data loading
    setTimeout(() => {
      setStats({
        networks: 24,
        workflows: 156,
        analyses: 89,
        computeUsage: 67,
      })
      setRecentActivity([
        { id: '1', type: 'workflow', action: 'completed', name: 'GRN Analysis #145', time: '2 min ago', user: 'John' },
        { id: '2', type: 'network', action: 'created', name: 'Cell Cycle Network v2', time: '15 min ago', user: 'Sarah' },
        { id: '3', type: 'analysis', action: 'started', name: 'ML Inference Batch', time: '1 hour ago', user: 'Mike' },
        { id: '4', type: 'workflow', action: 'failed', name: 'Hybrid Analysis #78', time: '2 hours ago', user: 'Anna' },
        { id: '5', type: 'network', action: 'updated', name: 'Signaling Pathway', time: '3 hours ago', user: 'John' },
      ])
      setRunningWorkflows([
        { id: '1', name: 'Qualitative Analysis #146', progress: 75, status: 'running', startedAt: '10 min ago' },
        { id: '2', name: 'GRNBoost2 Inference', progress: 45, status: 'running', startedAt: '25 min ago' },
        { id: '3', name: 'Multi-omics Integration', progress: 0, status: 'queued', startedAt: '' },
      ])
      setLoading(false)
    }, 1000)
  }, [])

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'network':
        return (
          <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        )
      case 'workflow':
        return (
          <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        )
      case 'analysis':
        return (
          <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        )
      default:
        return null
    }
  }

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>
      case 'created':
        return <Badge variant="primary">Created</Badge>
      case 'updated':
        return <Badge variant="info">Updated</Badge>
      case 'started':
        return <Badge variant="warning">Started</Badge>
      case 'failed':
        return <Badge variant="danger">Failed</Badge>
      default:
        return <Badge>{action}</Badge>
    }
  }

  return (
    <MainLayout
      title="Dashboard"
      breadcrumbs={[{ label: 'Dashboard' }]}
    >
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 md:p-8 text-white">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">Welcome to GenNet Cloud Platform</h1>
              <p className="text-blue-100 text-sm md:text-base max-w-xl">
                Cloud-native platform for multi-scale Gene Regulatory Network analysis with AI/ML integration and high-performance computing.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button variant="secondary" size="lg" as="a" href="/networks">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Network
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border-white/30 text-white hover:bg-white/10"
                as="a"
                href="/workflows"
              >
                Run Workflow
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {loading ? (
            <>
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} padding="md">
                  <Skeleton variant="text" width="40%" className="mb-2" />
                  <Skeleton variant="text" width="60%" height={32} className="mb-2" />
                  <Skeleton variant="text" width="30%" />
                </Card>
              ))}
            </>
          ) : (
            <>
              <StatCard
                title="Total Networks"
                value={stats?.networks || 0}
                change={{ value: 12, type: 'increase' }}
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
              />
              <StatCard
                title="Workflows Run"
                value={stats?.workflows || 0}
                change={{ value: 8, type: 'increase' }}
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                }
              />
              <StatCard
                title="Analyses Complete"
                value={stats?.analyses || 0}
                change={{ value: 5, type: 'increase' }}
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                }
              />
              <StatCard
                title="Compute Usage"
                value={`${stats?.computeUsage || 0}%`}
                description="of allocated resources"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                }
              />
            </>
          )}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Running Workflows */}
          <Card className="lg:col-span-2">
            <CardHeader action={<Button variant="ghost" size="sm">View All</Button>}>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Running Workflows</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex items-center gap-4">
                      <Skeleton variant="circular" width={40} height={40} />
                      <div className="flex-1">
                        <Skeleton variant="text" width="60%" className="mb-2" />
                        <Skeleton variant="rounded" height={8} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : runningWorkflows.length > 0 ? (
                runningWorkflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <CircularProgress value={workflow.progress} size={50} showLabel />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-slate-900 dark:text-slate-100 truncate">
                          {workflow.name}
                        </h3>
                        <Badge
                          variant={workflow.status === 'running' ? 'success' : 'warning'}
                          dot
                        >
                          {workflow.status}
                        </Badge>
                      </div>
                      <ProgressBar value={workflow.progress} size="sm" />
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        {workflow.status === 'running'
                          ? `Started ${workflow.startedAt}`
                          : 'Waiting in queue'}
                      </p>
                    </div>
                    <Button variant="ghost" size="icon-sm">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                      </svg>
                    </Button>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                  <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <p>No workflows running</p>
                  <Button variant="primary" size="sm" className="mt-4">
                    Start Workflow
                  </Button>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader action={<Button variant="ghost" size="sm">View All</Button>}>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Recent Activity</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="flex items-start gap-3">
                      <Skeleton variant="circular" width={40} height={40} />
                      <div className="flex-1">
                        <Skeleton variant="text" width="80%" className="mb-1" />
                        <Skeleton variant="text" width="40%" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-start gap-3 group">
                    {getActivityIcon(activity.type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-slate-900 dark:text-slate-100 truncate">
                          {activity.name}
                        </span>
                        {getActionBadge(activity.action)}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                        <span>by {activity.user}</span>
                        <span>•</span>
                        <span>{activity.time}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardBody>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link href="/networks" className="block">
            <Card hover padding="md" className="h-full">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">Browse Networks</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">View and manage GRNs</p>
                </div>
              </div>
            </Card>
          </Link>
          <Link href="/workflows" className="block">
            <Card hover padding="md" className="h-full">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">Run Analysis</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Start new workflows</p>
                </div>
              </div>
            </Card>
          </Link>
          <Link href="/models" className="block">
            <Card hover padding="md" className="h-full">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">ML Models</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">AI inference tools</p>
                </div>
              </div>
            </Card>
          </Link>
          <Link href="/data" className="block">
            <Card hover padding="md" className="h-full">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">Data Browser</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Explore datasets</p>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </div>
    </MainLayout>
  )
}

