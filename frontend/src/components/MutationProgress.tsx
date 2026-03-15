import { useEffect, useReducer, useRef } from "react"
import { Loader2, CheckCircle, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"

type Phase =
  | "idle"
  | "saving"
  | "saved"
  | "refetching"
  | "complete"
  | "error"

type Action =
  | { type: "START"; startTime: number }
  | { type: "SUCCESS"; duration: number }
  | { type: "REFETCH" }
  | { type: "COMPLETE" }
  | { type: "ERROR" }
  | { type: "RESET" }

interface State {
  phase: Phase
  saveDuration?: number
  startTime?: number
}

const initialState: State = { phase: "idle" }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "START":
      return { phase: "saving", startTime: action.startTime }
    case "SUCCESS":
      return { ...state, phase: "saved", saveDuration: action.duration }
    case "REFETCH":
      return { ...state, phase: "refetching" }
    case "COMPLETE":
      return { ...state, phase: "complete" }
    case "ERROR":
      return { ...state, phase: "error" }
    case "RESET":
      return initialState
    default:
      return state
  }
}

const phaseConfig: Record<
  Phase,
  { icon: typeof Loader2; text: string; iconClass: string }
> = {
  idle: {
    icon: Loader2,
    text: "Preparing...",
    iconClass: "animate-spin text-muted-foreground",
  },
  saving: {
    icon: Loader2,
    text: "Saving...",
    iconClass: "animate-spin text-primary",
  },
  saved: {
    icon: CheckCircle,
    text: "Saved to server",
    iconClass: "text-green-500",
  },
  refetching: {
    icon: RefreshCw,
    text: "Refreshing patient data...",
    iconClass: "animate-spin text-primary",
  },
  complete: {
    icon: CheckCircle,
    text: "Done",
    iconClass: "text-green-500",
  },
  error: {
    icon: CheckCircle,
    text: "Error",
    iconClass: "text-destructive",
  },
}

interface MutationProgressProps {
  isPending: boolean
  isSuccess: boolean
  isError: boolean
  errorMessage?: string
  onComplete: () => void
  className?: string
}

export function MutationProgress({
  isPending,
  isSuccess,
  isError,
  errorMessage,
  onComplete,
  className,
}: MutationProgressProps) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const hasStartedRef = useRef(false)
  const timersRef = useRef<Array<ReturnType<typeof setTimeout>>>([])

  const clearAllTimers = () => {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
  }

  useEffect(() => {
    return () => {
      clearAllTimers()
    }
  }, [])

  useEffect(() => {
    if (isPending && state.phase === "idle" && !hasStartedRef.current) {
      hasStartedRef.current = true
      dispatch({ type: "START", startTime: Date.now() })
    }
  }, [isPending, state.phase])

  useEffect(() => {
    if (!isPending && !isSuccess && !isError && state.phase !== "idle") {
      hasStartedRef.current = false
      clearAllTimers()
      dispatch({ type: "RESET" })
    }
  }, [isPending, isSuccess, isError, state.phase])

  useEffect(() => {
    if (isSuccess && state.phase === "saving" && state.startTime) {
      const duration = (Date.now() - state.startTime) / 1000
      dispatch({ type: "SUCCESS", duration })

      const refetchTimer = setTimeout(() => {
        dispatch({ type: "REFETCH" })
      }, 800)
      timersRef.current.push(refetchTimer)

      const completionTimer = setTimeout(() => {
        dispatch({ type: "COMPLETE" })
      }, 2000)
      timersRef.current.push(completionTimer)
    }
  }, [isSuccess, state.phase, state.startTime])

  useEffect(() => {
    if (state.phase === "complete") {
      const timer = setTimeout(onComplete, 500)
      timersRef.current.push(timer)
    }
  }, [state.phase, onComplete])

  useEffect(() => {
    if (isError && state.phase !== "idle" && state.phase !== "error") {
      clearAllTimers()
      dispatch({ type: "ERROR" })
    }
  }, [isError, state.phase])

  if (state.phase === "idle") return null

  const config = phaseConfig[state.phase]
  const Icon = config.icon

  const displayText =
    state.phase === "saved" && state.saveDuration !== undefined
      ? `Saved to server (${state.saveDuration.toFixed(1)}s)`
      : errorMessage && state.phase === "error"
        ? errorMessage
        : config.text

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm",
        className
      )}
      role="dialog"
      aria-modal="true"
      aria-labelledby="mutation-progress-title"
    >
      <div className="bg-card border rounded-lg shadow-lg p-6 min-w-[280px] max-w-[400px]">
        <div className="flex items-center gap-3">
          <Icon className={cn("size-5", config.iconClass)} />
          <span
            id="mutation-progress-title"
            className="text-sm font-medium"
            data-phase={state.phase}
          >
            {displayText}
          </span>
        </div>
      </div>
    </div>
  )
}
