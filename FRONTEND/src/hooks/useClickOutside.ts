import { useEffect, useRef, RefObject } from "react"

type ElementRef = RefObject<HTMLElement | null>

export function useClickOutside(
  refs: ElementRef | ElementRef[],
  handler: (event: MouseEvent | TouchEvent | KeyboardEvent) => void
) {
  const handlerRef = useRef(handler)
  handlerRef.current = handler

  useEffect(() => {
    const listener = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node | null
      if (!target) return

      const refList = Array.isArray(refs) ? refs : [refs]
      const clickedInside = refList.some(
        (ref) => ref.current && ref.current.contains(target)
      )

      if (!clickedInside) {
        handlerRef.current(event)
      }
    }

    document.addEventListener("mousedown", listener)
    document.addEventListener("touchstart", listener)

    return () => {
      document.removeEventListener("mousedown", listener)
      document.removeEventListener("touchstart", listener)
    }
  }, [refs])
}

export default useClickOutside
