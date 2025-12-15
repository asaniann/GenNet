'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { networkApi } from '@/lib/api'

interface Network {
  id: string
  name: string
  description?: string
  created_at: string
}

export default function NetworksPage() {
  const [networks, setNetworks] = useState<Network[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadNetworks()
  }, [])

  const loadNetworks = async () => {
    try {
      setLoading(true)
      const response = await networkApi.list()
      setNetworks(response.data || [])
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load networks')
      console.error('Error loading networks:', err)
    } finally {
      setLoading(false)
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
            <h1 className="text-4xl font-bold">Networks</h1>
            <p className="text-xl text-gray-600 mt-2">
              Create, edit, and manage Gene Regulatory Networks
            </p>
          </div>
          <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            Create Network
          </button>
        </div>

        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading networks...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            <p>Error: {error}</p>
            <button
              onClick={loadNetworks}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && (
          <>
            {networks.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500 mb-4">No networks found</p>
                <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                  Create Your First Network
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {networks.map((network) => (
                  <div
                    key={network.id}
                    className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
                  >
                    <h3 className="text-xl font-semibold mb-2">{network.name}</h3>
                    {network.description && (
                      <p className="text-gray-600 mb-4">{network.description}</p>
                    )}
                    <p className="text-sm text-gray-400 mb-4">
                      Created: {new Date(network.created_at).toLocaleDateString()}
                    </p>
                    <div className="flex gap-2">
                      <Link
                        href={`/networks/${network.id}`}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
                      >
                        View
                      </Link>
                      <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition text-sm">
                        Edit
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

