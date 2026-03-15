import { useEffect, useState } from "react"
import { useIsFetching, useIsMutating } from "@tanstack/react-query"
import { getSlowRequestElapsed, subscribe } from "@/api/request-timing"

function formatElapsed(ms: number): string {
  return (ms / 1000).toFixed(1) + "s"
}

export function GlobalLoadingBar() {
  const isFetching = useIsFetching()
  const isMutating = useIsMutating()
  const isLoading = isFetching > 0 || isMutating > 0
  const [elapsedMs, setElapsedMs] = useState<number | null>(null)

  useEffect(() => {
    if (!isLoading) {
      return
    }

    function updateElapsed() {
      setElapsedMs(getSlowRequestElapsed())
    }

    const interval = setInterval(updateElapsed, 100)
    const unsubscribe = subscribe(updateElapsed)

    return () => {
      clearInterval(interval)
      unsubscribe()
      setElapsedMs(null)
    }
  }, [isLoading])

  if (!isLoading) {
    return null
  }

  const label = elapsedMs != null 
    ? `Loading... (${formatElapsed(elapsedMs)})` 
    : "Loading"

  return (
    <div
      className="fixed left-0 top-0 z-50 w-full"
      role="progressbar"
      aria-busy="true"
      aria-label={label}
    >
      <div className="h-1 w-full overflow-hidden bg-transparent">
        <div className="animate-progress h-full w-1/4 bg-primary" />
      </div>
    </div>
  )
}
