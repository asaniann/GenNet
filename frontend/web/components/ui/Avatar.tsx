'use client'

import React from 'react'

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

export interface AvatarProps {
  src?: string
  alt?: string
  name?: string
  size?: AvatarSize
  status?: 'online' | 'offline' | 'away' | 'busy'
  className?: string
}

const sizeClasses: Record<AvatarSize, string> = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-xl',
}

const statusClasses: Record<string, string> = {
  online: 'bg-emerald-500',
  offline: 'bg-slate-400',
  away: 'bg-amber-500',
  busy: 'bg-red-500',
}

const statusSizeClasses: Record<AvatarSize, string> = {
  xs: 'w-1.5 h-1.5',
  sm: 'w-2 h-2',
  md: 'w-2.5 h-2.5',
  lg: 'w-3 h-3',
  xl: 'w-4 h-4',
}

const getInitials = (name: string): string => {
  const parts = name.trim().split(' ')
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase()
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

const getColorFromName = (name: string): string => {
  const colors = [
    'bg-blue-500',
    'bg-emerald-500',
    'bg-purple-500',
    'bg-amber-500',
    'bg-rose-500',
    'bg-cyan-500',
    'bg-indigo-500',
    'bg-teal-500',
  ]
  const index = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length
  return colors[index]
}

export const Avatar: React.FC<AvatarProps> = ({
  src,
  alt = 'Avatar',
  name,
  size = 'md',
  status,
  className = '',
}) => {
  const initials = name ? getInitials(name) : '?'
  const bgColor = name ? getColorFromName(name) : 'bg-slate-500'

  return (
    <div className={`relative inline-flex ${className}`}>
      {src ? (
        <img
          src={src}
          alt={alt}
          className={`
            ${sizeClasses[size]}
            rounded-full object-cover
            ring-2 ring-white dark:ring-slate-800
          `}
        />
      ) : (
        <div
          className={`
            ${sizeClasses[size]}
            ${bgColor}
            rounded-full flex items-center justify-center
            text-white font-medium
            ring-2 ring-white dark:ring-slate-800
          `}
        >
          {initials}
        </div>
      )}
      {status && (
        <span
          className={`
            absolute bottom-0 right-0
            ${statusSizeClasses[size]}
            ${statusClasses[status]}
            rounded-full
            ring-2 ring-white dark:ring-slate-800
          `}
        />
      )}
    </div>
  )
}

// Avatar Group
export interface AvatarGroupProps {
  avatars: Array<{ src?: string; name?: string }>
  max?: number
  size?: AvatarSize
}

export const AvatarGroup: React.FC<AvatarGroupProps> = ({ avatars, max = 4, size = 'md' }) => {
  const displayAvatars = avatars.slice(0, max)
  const remaining = avatars.length - max

  return (
    <div className="flex -space-x-2">
      {displayAvatars.map((avatar, index) => (
        <Avatar key={index} {...avatar} size={size} />
      ))}
      {remaining > 0 && (
        <div
          className={`
            ${sizeClasses[size]}
            rounded-full flex items-center justify-center
            bg-slate-200 dark:bg-slate-700
            text-slate-600 dark:text-slate-300 font-medium
            ring-2 ring-white dark:ring-slate-800
          `}
        >
          +{remaining}
        </div>
      )}
    </div>
  )
}
