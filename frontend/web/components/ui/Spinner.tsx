'use client'

import React from 'react'

type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

export interface SpinnerProps {
  size?: SpinnerSize
  color?: string
  className?: string
}

const sizeClasses: Record<SpinnerSize, string> = {
  xs: 'w-3 h-3 border',
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-2',
  xl: 'w-12 h-12 border-3',
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', color = 'blue', className = '' }) => {
  return (
    <div
      className={`
        animate-spin rounded-full
        border-slate-200 dark:border-slate-700
        border-t-${color}-600
        ${sizeClasses[size]}
        ${className}
      `}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}

// Full page loading overlay
export const LoadingOverlay: React.FC<{ message?: string }> = ({ message = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="xl" />
        <p className="text-slate-600 dark:text-slate-400 font-medium">{message}</p>
      </div>
    </div>
  )
}

// Inline loading indicator
export const LoadingIndicator: React.FC<{ text?: string }> = ({ text = 'Loading...' }) => {
  return (
    <div className="flex items-center justify-center gap-3 py-8">
      <Spinner size="md" />
      <span className="text-slate-600 dark:text-slate-400">{text}</span>
    </div>
  )
}
