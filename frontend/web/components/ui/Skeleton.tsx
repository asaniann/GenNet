'use client'

import React from 'react'

export interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded'
  width?: string | number
  height?: string | number
  className?: string
  lines?: number
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width,
  height,
  className = '',
  lines = 1,
}) => {
  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-none',
    rounded: 'rounded-xl',
  }

  const style: React.CSSProperties = {
    width: width || (variant === 'text' ? '100%' : undefined),
    height: height || (variant === 'circular' ? width : undefined),
  }

  if (lines > 1 && variant === 'text') {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`animate-pulse bg-slate-200 dark:bg-slate-700 ${variantClasses.text}`}
            style={{
              width: i === lines - 1 ? '60%' : '100%',
              height: height || '1rem',
            }}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      className={`animate-pulse bg-slate-200 dark:bg-slate-700 ${variantClasses[variant]} ${className}`}
      style={style}
    />
  )
}

// Skeleton variants for common use cases
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm ${className}`}>
    <div className="flex items-center gap-4 mb-4">
      <Skeleton variant="circular" width={48} height={48} />
      <div className="flex-1">
        <Skeleton variant="text" width="60%" className="mb-2" />
        <Skeleton variant="text" width="40%" />
      </div>
    </div>
    <Skeleton variant="text" lines={3} />
    <div className="flex gap-3 mt-4">
      <Skeleton variant="rounded" width={80} height={36} />
      <Skeleton variant="rounded" width={80} height={36} />
    </div>
  </div>
)

export const SkeletonTable: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4,
}) => (
  <div className="bg-white dark:bg-slate-800 rounded-xl overflow-hidden">
    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} variant="text" width="20%" height={20} />
        ))}
      </div>
    </div>
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div
        key={rowIndex}
        className="p-4 border-b border-slate-200 dark:border-slate-700 last:border-0"
      >
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} variant="text" width="20%" />
          ))}
        </div>
      </div>
    ))}
  </div>
)

export const SkeletonList: React.FC<{ items?: number }> = ({ items = 5 }) => (
  <div className="space-y-4">
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="flex items-center gap-4">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="flex-1">
          <Skeleton variant="text" width="70%" className="mb-2" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
    ))}
  </div>
)
