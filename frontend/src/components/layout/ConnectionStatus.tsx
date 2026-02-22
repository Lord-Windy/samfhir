import { useHealthCheck } from "@/hooks/use-health"

export function ConnectionStatus() {
  const { data, isLoading, isError } = useHealthCheck()

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
  } else if (data.status === "healthy" && data.redis === "connected") {
    status = "connected"
    label = "Connected"
  } else if (data.status === "healthy" || data.redis === "connected") {
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

  return (
    <div className="flex items-center gap-2">
      <div className={`h-2 w-2 rounded-full ${colorClasses[status]}`} />
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  )
}
