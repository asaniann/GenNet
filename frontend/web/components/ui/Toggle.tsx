'use client'

import React from 'react'

export interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
  description?: string
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: {
    toggle: 'w-8 h-4',
    dot: 'h-3 w-3',
    translateActive: 'translate-x-4',
    translateInactive: 'translate-x-0.5',
  },
  md: {
    toggle: 'w-11 h-6',
    dot: 'h-5 w-5',
    translateActive: 'translate-x-5',
    translateInactive: 'translate-x-0.5',
  },
  lg: {
    toggle: 'w-14 h-7',
    dot: 'h-6 w-6',
    translateActive: 'translate-x-7',
    translateInactive: 'translate-x-0.5',
  },
}

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md',
  className = '',
}) => {
  const sizes = sizeClasses[size]

  return (
    <label
      className={`
        inline-flex items-start gap-3 cursor-pointer
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={`
          relative inline-flex items-center shrink-0 rounded-full
          transition-colors duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${sizes.toggle}
          ${checked ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'}
        `}
      >
        <span
          className={`
            inline-block rounded-full bg-white shadow transform
            transition-transform duration-200 ease-in-out
            ${sizes.dot}
            ${checked ? sizes.translateActive : sizes.translateInactive}
          `}
        />
      </button>
      {(label || description) && (
        <div className="flex flex-col">
          {label && (
            <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
              {label}
            </span>
          )}
          {description && (
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {description}
            </span>
          )}
        </div>
      )}
    </label>
  )
}
