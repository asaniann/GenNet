'use client'

import React, { useState, useRef, useEffect } from 'react'

export interface DropdownProps {
  trigger: React.ReactNode
  children: React.ReactNode
  align?: 'left' | 'right'
  className?: string
}

export const Dropdown: React.FC<DropdownProps> = ({
  trigger,
  children,
  align = 'left',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  return (
    <div ref={dropdownRef} className={`relative inline-block ${className}`}>
      <div onClick={() => setIsOpen(!isOpen)}>{trigger}</div>
      {isOpen && (
        <div
          className={`
            absolute z-50 mt-2 
            bg-white dark:bg-slate-800 
            rounded-xl shadow-xl 
            border border-slate-200 dark:border-slate-700
            min-w-[200px] py-1 overflow-hidden
            animate-scale-in origin-top-right
            ${align === 'right' ? 'right-0' : 'left-0'}
          `}
        >
          {React.Children.map(children, (child) =>
            React.isValidElement(child)
              ? React.cloneElement(child, {
                  onClick: (e: React.MouseEvent) => {
                    child.props.onClick?.(e)
                    setIsOpen(false)
                  },
                } as any)
              : child
          )}
        </div>
      )}
    </div>
  )
}

export interface DropdownItemProps {
  children: React.ReactNode
  icon?: React.ReactNode
  onClick?: () => void
  variant?: 'default' | 'danger'
  disabled?: boolean
  className?: string
}

export const DropdownItem: React.FC<DropdownItemProps> = ({
  children,
  icon,
  onClick,
  variant = 'default',
  disabled = false,
  className = '',
}) => {
  const variantClasses = {
    default: 'text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700',
    danger: 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20',
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`
        w-full px-4 py-2.5 text-sm text-left
        flex items-center gap-3
        cursor-pointer transition-colors duration-150
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {icon && <span className="flex-shrink-0 w-5 h-5">{icon}</span>}
      {children}
    </button>
  )
}

export const DropdownDivider: React.FC = () => (
  <div className="my-1 border-t border-slate-200 dark:border-slate-700" />
)

export const DropdownLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="px-4 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
    {children}
  </div>
)
