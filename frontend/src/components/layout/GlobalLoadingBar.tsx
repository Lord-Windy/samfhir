import { useIsFetching, useIsMutating } from "@tanstack/react-query"

export function GlobalLoadingBar() {
  const isFetching = useIsFetching()
  const isMutating = useIsMutating()
  const isLoading = isFetching > 0 || isMutating > 0

  if (!isLoading) {
    return null
  }

  return (
    <div className="fixed left-0 top-0 z-50 w-full">
      <div className="h-1 w-full overflow-hidden bg-transparent">
        <div className="animate-progress h-full w-1/4 bg-primary" />
      </div>
    </div>
  )
}
