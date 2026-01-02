'use client'

import React from 'react'

export interface ProgressBarProps {
  value: number
  max?: number
  showLabel?: boolean
  label?: string
  size?: 'sm' | 'md' | 'lg'
  color?: 'blue' | 'green' | 'amber' | 'red' | 'purple'
  animated?: boolean
  className?: string
}

const sizeClasses = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
}

const colorClasses = {
  blue: 'bg-blue-600',
  green: 'bg-emerald-600',
  amber: 'bg-amber-500',
  red: 'bg-red-600',
  purple: 'bg-purple-600',
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  showLabel = false,
  label,
  size = 'md',
  color = 'blue',
  animated = false,
  className = '',
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  return (
    <div className={className}>
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {label || 'Progress'}
          </span>
          {showLabel && (
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div
        className={`
          w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden
          ${sizeClasses[size]}
        `}
      >
        <div
          className={`
            ${sizeClasses[size]}
            ${colorClasses[color]}
            rounded-full transition-all duration-500 ease-out
            ${animated ? 'animate-pulse' : ''}
          `}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  )
}

// Circular Progress
export interface CircularProgressProps {
  value: number
  max?: number
  size?: number
  strokeWidth?: number
  showLabel?: boolean
  color?: 'blue' | 'green' | 'amber' | 'red' | 'purple'
  className?: string
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  max = 100,
  size = 60,
  strokeWidth = 6,
  showLabel = true,
  color = 'blue',
  className = '',
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (percentage / 100) * circumference

  const strokeColors = {
    blue: 'stroke-blue-600',
    green: 'stroke-emerald-600',
    amber: 'stroke-amber-500',
    red: 'stroke-red-600',
    purple: 'stroke-purple-600',
  }

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          className="stroke-slate-200 dark:stroke-slate-700"
          strokeWidth={strokeWidth}
          fill="none"
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
        <circle
          className={`${strokeColors[color]} transition-all duration-500 ease-out`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
          r={radius}
          cx={size / 2}
          cy={size / 2}
          style={{
            strokeDasharray: circumference,
            strokeDashoffset: offset,
          }}
        />
      </svg>
      {showLabel && (
        <span className="absolute text-sm font-semibold text-slate-700 dark:text-slate-300">
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  )
}
