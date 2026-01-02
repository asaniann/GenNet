'use client'

import React, { forwardRef } from 'react'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  onRightIconClick?: () => void
  fullWidth?: boolean
  variant?: 'default' | 'filled' | 'ghost'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      onRightIconClick,
      fullWidth = true,
      variant = 'default',
      className = '',
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`

    const baseClasses = `
      px-4 py-2.5 rounded-lg transition-all duration-200
      placeholder:text-slate-400 dark:placeholder:text-slate-500
      focus:outline-none focus:ring-2 focus:ring-offset-0
      disabled:bg-slate-100 dark:disabled:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-60
      ${fullWidth ? 'w-full' : ''}
    `

    const variantClasses = {
      default: `
        border border-slate-300 dark:border-slate-600
        bg-white dark:bg-slate-800 
        text-slate-900 dark:text-slate-100
        focus:border-blue-500 focus:ring-blue-500/20
        ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}
      `,
      filled: `
        border-0
        bg-slate-100 dark:bg-slate-800 
        text-slate-900 dark:text-slate-100
        focus:ring-blue-500/20 focus:bg-white dark:focus:bg-slate-700
        ${error ? 'bg-red-50 dark:bg-red-900/20 focus:ring-red-500/20' : ''}
      `,
      ghost: `
        border-0 border-b-2 border-slate-200 dark:border-slate-700 rounded-none
        bg-transparent
        text-slate-900 dark:text-slate-100
        focus:border-blue-500 focus:ring-0
        ${error ? 'border-red-500' : ''}
      `,
    }

    return (
      <div className={`${fullWidth ? 'w-full' : 'inline-block'}`}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            className={`
              ${baseClasses}
              ${variantClasses[variant]}
              ${leftIcon ? 'pl-10' : ''}
              ${rightIcon ? 'pr-10' : ''}
              ${className}
            `}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
            {...props}
          />
          {rightIcon && (
            <div
              className={`absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 ${
                onRightIconClick ? 'cursor-pointer hover:text-slate-600' : 'pointer-events-none'
              }`}
              onClick={onRightIconClick}
            >
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p id={`${inputId}-error`} className="mt-1.5 text-sm text-red-600 dark:text-red-400 flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={`${inputId}-hint`} className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
            {hint}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
