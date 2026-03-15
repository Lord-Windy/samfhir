import { createContext, useContext, useCallback, useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useHealthCheck } from "@/hooks/use-health"
import { AlertCircle, Wifi, WifiOff, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface QueuedMutation {
  id: string
  mutationFn: () => Promise<unknown>
  description: string
  timestamp: number
}

interface OfflineQueueContextType {
  isOnline: boolean
  queueMutation: (mutation: Omit<QueuedMutation, "id" | "timestamp">) => string
  removeMutation: (id: string) => void
  pendingMutations: QueuedMutation[]
  retryAll: () => Promise<void>
  retryCount: number
}

const OfflineQueueContext = createContext<OfflineQueueContextType | null>(null)

export function useOfflineQueue() {
  const context = useContext(OfflineQueueContext)
  if (!context) {
    throw new Error("useOfflineQueue must be used within OfflineQueueProvider")
  }
  return context
}

interface OfflineQueueProviderProps {
  children: React.ReactNode
}

export function OfflineQueueProvider({ children }: OfflineQueueProviderProps) {
  const [pendingMutations, setPendingMutations] = useState<QueuedMutation[]>([])
  const [retryCount, setRetryCount] = useState(0)
  const { isError } = useHealthCheck()
  const queryClient = useQueryClient()
  const processingRef = useRef(false)

  const isOnline = !isError

  const removeMutation = useCallback((id: string) => {
    setPendingMutations((prev) => prev.filter((m) => m.id !== id))
  }, [])

  const retryAllMutations = useCallback(async () => {
    if (processingRef.current || pendingMutations.length === 0) return

    processingRef.current = true
    const mutationsToProcess = [...pendingMutations]

    for (const mutation of mutationsToProcess) {
      try {
        await mutation.mutationFn()
        setPendingMutations((prev) => prev.filter((m) => m.id !== mutation.id))
      } catch {
        setRetryCount((c) => c + 1)
      }
    }

    processingRef.current = false
    queryClient.invalidateQueries()
  }, [pendingMutations, queryClient])

  const queueMutation = useCallback(
    (mutation: Omit<QueuedMutation, "id" | "timestamp">): string => {
      if (isOnline) {
        mutation.mutationFn()
        return ""
      }

      const id = `mutation-${Date.now()}-${Math.random().toString(36).slice(2)}`
      const queuedMutation: QueuedMutation = {
        ...mutation,
        id,
        timestamp: Date.now(),
      }

      setPendingMutations((prev) => [...prev, queuedMutation])
      return id
    },
    [isOnline],
  )

  return (
    <OfflineQueueContext.Provider
      value={{
        isOnline,
        queueMutation,
        removeMutation,
        pendingMutations,
        retryAll: retryAllMutations,
        retryCount,
      }}
    >
      {children}
    </OfflineQueueContext.Provider>
  )
}

export function ConnectionStatus() {
  const { data, isLoading, isError } = useHealthCheck()
  const { isOnline, pendingMutations, retryAll } = useOfflineQueue()
  const [isRetrying, setIsRetrying] = useState(false)

  let status: "connected" | "degraded" | "disconnected" = "connected"
  let label = "Connected"

  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
        <span className="text-xs text-muted-foreground">Checking...</span>
      </div>
    )
  }

  if (isError || !data) {
    status = "disconnected"
    label = "Disconnected"
  } else if (data.status === "ok" && data.redis === "connected") {
    status = "connected"
    label = "Connected"
  } else if (data.status === "ok" || data.redis === "connected") {
    status = "degraded"
    label = "Degraded"
  } else {
    status = "disconnected"
    label = "Disconnected"
  }

  const colorClasses = {
    connected: "bg-green-500",
    degraded: "bg-amber-500",
    disconnected: "bg-red-500",
  }

  const handleRetryAll = async () => {
    setIsRetrying(true)
    await retryAll()
    setIsRetrying(false)
  }

  return (
    <>
      {!isOnline && (
        <div className="fixed left-0 right-0 top-14 z-50 flex items-center justify-center gap-3 bg-destructive px-4 py-2 text-destructive-foreground">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm font-medium">
            You are offline. Changes will be saved when connection is restored.
          </span>
          {pendingMutations.length > 0 && (
            <span className="text-sm">
              ({pendingMutations.length} pending change
              {pendingMutations.length !== 1 ? "s" : ""})
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetryAll}
            disabled={isRetrying || pendingMutations.length === 0}
            className="ml-2 h-7 border-destructive-foreground/30 bg-transparent text-destructive-foreground hover:bg-destructive-foreground/10"
          >
            {isRetrying ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="h-3 w-3" />
            )}
            <span className="ml-1">Retry</span>
          </Button>
        </div>
      )}
      <div className="flex items-center gap-2">
        {status === "connected" ? (
          <Wifi className="h-3.5 w-3.5 text-green-500" />
        ) : status === "disconnected" ? (
          <WifiOff className="h-3.5 w-3.5 text-red-500" />
        ) : (
          <div className={`h-2 w-2 rounded-full ${colorClasses[status]}`} />
        )}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </>
  )
}
