'use client'

import { useState } from 'react'
import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">GenNet Cloud Platform</h1>
        <p className="text-xl mb-8">
          Cloud-native platform for multi-scale Gene Regulatory Network analysis
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link href="/networks" className="p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-2xl font-semibold mb-2">Networks</h2>
            <p>Create, edit, and manage GRN networks</p>
          </Link>
          
          <Link href="/workflows" className="p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-2xl font-semibold mb-2">Workflows</h2>
            <p>Run qualitative, hybrid, and ML analyses</p>
          </Link>
          
          <Link href="/analyses" className="p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-2xl font-semibold mb-2">Analyses</h2>
            <p>View and explore analysis results</p>
          </Link>
        </div>
      </div>
    </main>
  )
}

