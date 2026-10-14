import { useEffect, useRef, RefObject } from "react"

/**
 * Traps keyboard Tab navigation within the referenced container while open.
 * Closes the modal on Escape key press, auto-focuses the first interactive element,
 * and restores focus to the previously active element upon closing.
 */
export interface FocusTrapOptions {
  isOpen: boolean
  onClose?: () => void
}

export function useFocusTrap<T extends HTMLElement = HTMLElement>(
  isOpenOrOptions: boolean | FocusTrapOptions,
  onCloseArg?: () => void
): RefObject<T | null> {
  const isOpen = typeof isOpenOrOptions === "boolean" ? isOpenOrOptions : isOpenOrOptions.isOpen
  const onClose = typeof isOpenOrOptions === "boolean" ? onCloseArg : isOpenOrOptions.onClose

  const containerRef = useRef<T | null>(null)
  const previousFocusedElement = useRef<HTMLElement | null>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    if (!isOpen) return

    // Store the element that had focus before opening the modal
    previousFocusedElement.current = document.activeElement as HTMLElement | null

    const container = containerRef.current
    if (!container) return

    const focusableSelector =
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

    // Delay focus slightly to ensure DOM is rendered and animations settle
    const timer = setTimeout(() => {
      if (!container) return
      const focusable = Array.from(
        container.querySelectorAll<HTMLElement>(focusableSelector)
      ).filter((el) => {
        const style = window.getComputedStyle(el)
        return style.display !== "none" && style.visibility !== "hidden"
      })

      if (focusable.length > 0) {
        focusable[0].focus()
      } else {
        container.focus()
      }
    }, 50)

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (onCloseRef.current) {
          e.preventDefault()
          e.stopPropagation()
          onCloseRef.current()
        }
        return
      }

      if (e.key === "Tab") {
        const focusable = Array.from(
          container.querySelectorAll<HTMLElement>(focusableSelector)
        ).filter((el) => {
          const style = window.getComputedStyle(el)
          return style.display !== "none" && style.visibility !== "hidden"
        })

        if (focusable.length === 0) {
          e.preventDefault()
          return
        }

        const firstElement = focusable[0]
        const lastElement = focusable[focusable.length - 1]

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault()
            lastElement.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault()
            firstElement.focus()
          }
        }
      }
    }

    document.addEventListener("keydown", handleKeyDown)

    return () => {
      clearTimeout(timer)
      document.removeEventListener("keydown", handleKeyDown)

      // Restore focus to previous element when modal unmounts
      if (previousFocusedElement.current && typeof previousFocusedElement.current.focus === "function") {
        previousFocusedElement.current.focus()
      }
    }
  }, [isOpen])

  return containerRef
}

export default useFocusTrap
