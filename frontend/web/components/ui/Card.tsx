'use client'

import React from 'react'

export interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
  onClick?: () => void
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, className = '', hover = false, padding = 'none', onClick }, ref) => {
    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    }

    return (
      <div
        ref={ref}
        onClick={onClick}
        className={`
          bg-white dark:bg-slate-800 rounded-xl shadow-sm 
          border border-slate-200 dark:border-slate-700
          transition-all duration-200
          ${hover ? 'hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-600 cursor-pointer' : ''}
          ${paddingClasses[padding]}
          ${className}
        `}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

export interface CardHeaderProps {
  children: React.ReactNode
  className?: string
  action?: React.ReactNode
}

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '', action }) => (
  <div
    className={`px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between ${className}`}
  >
    <div>{children}</div>
    {action && <div>{action}</div>}
  </div>
)

export interface CardBodyProps {
  children: React.ReactNode
  className?: string
}

export const CardBody: React.FC<CardBodyProps> = ({ children, className = '' }) => (
  <div className={`p-6 ${className}`}>{children}</div>
)

export interface CardFooterProps {
  children: React.ReactNode
  className?: string
}

export const CardFooter: React.FC<CardFooterProps> = ({ children, className = '' }) => (
  <div
    className={`px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 rounded-b-xl ${className}`}
  >
    {children}
  </div>
)
