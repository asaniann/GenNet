'use client'

import React, { useState, createContext, useContext } from 'react'

interface TabsContextValue {
  activeTab: string
  setActiveTab: (id: string) => void
}

const TabsContext = createContext<TabsContextValue | null>(null)

export interface TabsProps {
  children: React.ReactNode
  defaultTab?: string
  value?: string
  onChange?: (tabId: string) => void
  className?: string
  variant?: 'default' | 'pills' | 'underline'
}

export const Tabs: React.FC<TabsProps> = ({
  children,
  defaultTab,
  value,
  onChange,
  className = '',
  variant = 'default',
}) => {
  const [internalActiveTab, setInternalActiveTab] = useState(defaultTab || '')
  
  const activeTab = value !== undefined ? value : internalActiveTab

  const handleTabChange = (tabId: string) => {
    if (value === undefined) {
      setInternalActiveTab(tabId)
    }
    onChange?.(tabId)
  }

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleTabChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export interface TabListProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'pills' | 'underline'
}

export const TabList: React.FC<TabListProps> = ({ children, className = '', variant = 'default' }) => {
  const variantClasses = {
    default: 'flex border-b border-slate-200 dark:border-slate-700 gap-1',
    pills: 'flex gap-2 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg',
    underline: 'flex gap-6',
  }

  return <div className={`${variantClasses[variant]} ${className}`}>{children}</div>
}

export interface TabProps {
  id: string
  children: React.ReactNode
  disabled?: boolean
  icon?: React.ReactNode
  variant?: 'default' | 'pills' | 'underline'
}

export const Tab: React.FC<TabProps> = ({ id, children, disabled = false, icon, variant = 'default' }) => {
  const context = useContext(TabsContext)
  if (!context) throw new Error('Tab must be used within Tabs')

  const { activeTab, setActiveTab } = context
  const isActive = activeTab === id

  const baseClasses = 'flex items-center gap-2 font-medium transition-all duration-200 cursor-pointer'

  const variantClasses = {
    default: `
      px-4 py-2.5 text-sm border-b-2 -mb-px
      ${isActive 
        ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400' 
        : 'text-slate-600 dark:text-slate-400 border-transparent hover:text-slate-900 dark:hover:text-slate-100'}
      ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
    `,
    pills: `
      px-4 py-2 text-sm rounded-md
      ${isActive 
        ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm' 
        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'}
      ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
    `,
    underline: `
      py-3 text-sm
      ${isActive 
        ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 -mb-px' 
        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'}
      ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
    `,
  }

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      aria-disabled={disabled}
      disabled={disabled}
      onClick={() => !disabled && setActiveTab(id)}
      className={`${baseClasses} ${variantClasses[variant]}`}
    >
      {icon}
      {children}
    </button>
  )
}

export interface TabPanelProps {
  id: string
  children: React.ReactNode
  className?: string
}

export const TabPanel: React.FC<TabPanelProps> = ({ id, children, className = '' }) => {
  const context = useContext(TabsContext)
  if (!context) throw new Error('TabPanel must be used within Tabs')

  const { activeTab } = context

  if (activeTab !== id) return null

  return (
    <div role="tabpanel" className={`animate-fade-in ${className}`}>
      {children}
    </div>
  )
}
