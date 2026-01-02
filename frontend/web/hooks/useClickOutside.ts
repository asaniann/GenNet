import { useEffect, useRef, RefObject } from 'react'

type Handler = (event: MouseEvent | TouchEvent) => void

/**
 * Custom hook to detect clicks outside of an element
 * 
 * @param handler - Callback function to call when click is detected outside
 * @param enabled - Whether the hook is enabled (default: true)
 * @returns Ref to attach to the element
 * 
 * @example
 * const dropdownRef = useClickOutside<HTMLDivElement>(() => {
 *   setIsOpen(false)
 * })
 * 
 * return <div ref={dropdownRef}>...</div>
 */
export function useClickOutside<T extends HTMLElement = HTMLElement>(
  handler: Handler,
  enabled: boolean = true
): RefObject<T> {
  const ref = useRef<T>(null)

  useEffect(() => {
    if (!enabled) return

    const listener = (event: MouseEvent | TouchEvent) => {
      const el = ref.current

      // Do nothing if clicking ref's element or descendent elements
      if (!el || el.contains(event.target as Node)) {
        return
      }

      handler(event)
    }

    document.addEventListener('mousedown', listener)
    document.addEventListener('touchstart', listener)

    return () => {
      document.removeEventListener('mousedown', listener)
      document.removeEventListener('touchstart', listener)
    }
  }, [handler, enabled])

  return ref
}

/**
 * Custom hook to detect clicks outside of multiple elements
 * 
 * @param handler - Callback function to call when click is detected outside
 * @param enabled - Whether the hook is enabled
 * @returns Array of refs to attach to elements
 * 
 * @example
 * const [buttonRef, menuRef] = useClickOutsideMultiple<HTMLButtonElement, HTMLDivElement>(
 *   () => setIsOpen(false),
 *   isOpen
 * )
 */
export function useClickOutsideMultiple<
  T1 extends HTMLElement = HTMLElement,
  T2 extends HTMLElement = HTMLElement
>(
  handler: Handler,
  enabled: boolean = true
): [RefObject<T1>, RefObject<T2>] {
  const ref1 = useRef<T1>(null)
  const ref2 = useRef<T2>(null)

  useEffect(() => {
    if (!enabled) return

    const listener = (event: MouseEvent | TouchEvent) => {
      const el1 = ref1.current
      const el2 = ref2.current

      // Do nothing if clicking any of the ref elements or their descendants
      if (
        !el1 ||
        !el2 ||
        el1.contains(event.target as Node) ||
        el2.contains(event.target as Node)
      ) {
        return
      }

      handler(event)
    }

    document.addEventListener('mousedown', listener)
    document.addEventListener('touchstart', listener)

    return () => {
      document.removeEventListener('mousedown', listener)
      document.removeEventListener('touchstart', listener)
    }
  }, [handler, enabled])

  return [ref1, ref2]
}
