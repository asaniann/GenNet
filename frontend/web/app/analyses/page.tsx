'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Analysis {
  id: string
  name: string
  type: string
  status: string
  created_at: string
  results?: any
}

export default function AnalysesPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // TODO: Replace with actual API call when analysis endpoint is available
    // For now, show empty state
    setLoading(false)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">
              ← Back to Home
            </Link>
            <h1 className="text-4xl font-bold">Analyses</h1>
            <p className="text-xl text-gray-600 mt-2">
              View and explore analysis results
            </p>
          </div>
        </div>

        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading analyses...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            <p>Error: {error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {analyses.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500 mb-4">No analyses found</p>
                <p className="text-sm text-gray-400 mb-4">
                  Run a workflow to generate analysis results
                </p>
                <Link
                  href="/workflows"
                  className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Go to Workflows
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {analyses.map((analysis) => (
                  <div
                    key={analysis.id}
                    className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-xl font-semibold">{analysis.name}</h3>
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                          analysis.status
                        )}`}
                      >
                        {analysis.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mb-2 capitalize">
                      Type: {analysis.type}
                    </p>
                    <p className="text-sm text-gray-400 mb-4">
                      Created: {new Date(analysis.created_at).toLocaleDateString()}
                    </p>
                    <div className="flex gap-2">
                      <Link
                        href={`/analyses/${analysis.id}`}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
                      >
                        View Results
                      </Link>
                      <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition text-sm">
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}

