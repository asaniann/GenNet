import { useState, useCallback } from 'react'

interface CopyToClipboardResult {
  copiedText: string | null
  copyToClipboard: (text: string) => Promise<boolean>
  isCopied: boolean
  error: Error | null
}

/**
 * Custom hook to copy text to clipboard
 * 
 * @param resetDelay - Time in ms before isCopied resets (default: 2000)
 * @returns Object with copy function and state
 * 
 * @example
 * const { copyToClipboard, isCopied } = useCopyToClipboard()
 * 
 * <button onClick={() => copyToClipboard('Hello!')}>
 *   {isCopied ? 'Copied!' : 'Copy'}
 * </button>
 */
export function useCopyToClipboard(resetDelay: number = 2000): CopyToClipboardResult {
  const [copiedText, setCopiedText] = useState<string | null>(null)
  const [isCopied, setIsCopied] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const copyToClipboard = useCallback(
    async (text: string): Promise<boolean> => {
      // Check if clipboard API is available
      if (!navigator?.clipboard) {
        // Fallback for older browsers
        try {
          const textArea = document.createElement('textarea')
          textArea.value = text
          textArea.style.position = 'fixed'
          textArea.style.left = '-999999px'
          textArea.style.top = '-999999px'
          document.body.appendChild(textArea)
          textArea.focus()
          textArea.select()

          const success = document.execCommand('copy')
          document.body.removeChild(textArea)

          if (success) {
            setCopiedText(text)
            setIsCopied(true)
            setError(null)

            setTimeout(() => {
              setIsCopied(false)
            }, resetDelay)

            return true
          } else {
            throw new Error('Copy command failed')
          }
        } catch (err) {
          setError(err instanceof Error ? err : new Error('Failed to copy'))
          return false
        }
      }

      try {
        await navigator.clipboard.writeText(text)
        setCopiedText(text)
        setIsCopied(true)
        setError(null)

        setTimeout(() => {
          setIsCopied(false)
        }, resetDelay)

        return true
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to copy'))
        setIsCopied(false)
        setCopiedText(null)
        return false
      }
    },
    [resetDelay]
  )

  return {
    copiedText,
    copyToClipboard,
    isCopied,
    error,
  }
}

/**
 * Utility function to copy text (non-hook version)
 */
export async function copyTextToClipboard(text: string): Promise<boolean> {
  if (!navigator?.clipboard) {
    try {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      document.body.appendChild(textArea)
      textArea.select()
      const success = document.execCommand('copy')
      document.body.removeChild(textArea)
      return success
    } catch {
      return false
    }
  }

  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}
