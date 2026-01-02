import { useEffect, useCallback } from 'react'

type KeyHandler = (event: KeyboardEvent) => void

interface KeyPressOptions {
  enabled?: boolean
  target?: Window | HTMLElement | null
  eventType?: 'keydown' | 'keyup' | 'keypress'
  preventDefault?: boolean
}

/**
 * Custom hook to handle keyboard shortcuts
 * 
 * @param key - The key or key combination to listen for
 * @param handler - Callback function when key is pressed
 * @param options - Configuration options
 * 
 * @example
 * // Simple key press
 * useKeyPress('Escape', () => closeModal())
 * 
 * // Key with modifier
 * useKeyPress('k', () => openSearch(), { ctrlKey: true })
 * 
 * // Multiple keys
 * useKeyPress(['ArrowUp', 'ArrowDown'], handleNavigation)
 */
export function useKeyPress(
  key: string | string[],
  handler: KeyHandler,
  options: KeyPressOptions & {
    ctrlKey?: boolean
    metaKey?: boolean
    shiftKey?: boolean
    altKey?: boolean
  } = {}
): void {
  const {
    enabled = true,
    target = typeof window !== 'undefined' ? window : null,
    eventType = 'keydown',
    preventDefault = false,
    ctrlKey = false,
    metaKey = false,
    shiftKey = false,
    altKey = false,
  } = options

  const keys = Array.isArray(key) ? key : [key]

  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      // Check if the pressed key matches any of our target keys
      const keyMatches = keys.some(
        (k) => event.key === k || event.code === k
      )

      if (!keyMatches) return

      // Check modifier keys
      if (ctrlKey && !event.ctrlKey) return
      if (metaKey && !event.metaKey) return
      if (shiftKey && !event.shiftKey) return
      if (altKey && !event.altKey) return

      // If we're requiring no modifiers but one is pressed, return
      if (!ctrlKey && !metaKey && (event.ctrlKey || event.metaKey)) {
        // Allow if the key is Escape or similar non-text keys
        if (!['Escape', 'Tab', 'Enter', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
          return
        }
      }

      if (preventDefault) {
        event.preventDefault()
      }

      handler(event)
    },
    [keys, handler, ctrlKey, metaKey, shiftKey, altKey, preventDefault]
  )

  useEffect(() => {
    if (!enabled || !target) return

    target.addEventListener(eventType as any, handleKeyPress as any)

    return () => {
      target.removeEventListener(eventType as any, handleKeyPress as any)
    }
  }, [enabled, target, eventType, handleKeyPress])
}

/**
 * Hook for common keyboard shortcuts
 */
export function useEscapeKey(handler: () => void, enabled: boolean = true): void {
  useKeyPress('Escape', handler, { enabled })
}

export function useEnterKey(handler: KeyHandler, enabled: boolean = true): void {
  useKeyPress('Enter', handler, { enabled })
}

export function useSaveShortcut(handler: () => void, enabled: boolean = true): void {
  useKeyPress('s', handler, { enabled, ctrlKey: true, preventDefault: true })
  useKeyPress('s', handler, { enabled, metaKey: true, preventDefault: true })
}

export function useSearchShortcut(handler: () => void, enabled: boolean = true): void {
  useKeyPress('k', handler, { enabled, ctrlKey: true, preventDefault: true })
  useKeyPress('k', handler, { enabled, metaKey: true, preventDefault: true })
}

export function useArrowNavigation(
  onUp: () => void,
  onDown: () => void,
  enabled: boolean = true
): void {
  useKeyPress('ArrowUp', onUp, { enabled, preventDefault: true })
  useKeyPress('ArrowDown', onDown, { enabled, preventDefault: true })
}
