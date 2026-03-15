import { screen, waitFor } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import { renderWithProviders } from "@/test-utils"
import { ConnectionStatus, useOfflineQueue, OfflineQueueProvider } from "./ConnectionStatus"
import { describe, it, expect, vi } from "vitest"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { renderHook, act } from "@testing-library/react"

describe("ConnectionStatus", () => {
  it('shows "Connected" when API and Redis are healthy', async () => {
    renderWithProviders(<ConnectionStatus />)
    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument()
    })
  })

  it('shows "Degraded" when API is ok but Redis is not', async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json({ status: "ok", redis: "disconnected" }),
      ),
    )
    renderWithProviders(<ConnectionStatus />)
    await waitFor(() => {
      expect(screen.getByText("Degraded")).toBeInTheDocument()
    })
  })

  it('shows "Disconnected" when API request fails', async () => {
    server.use(
      http.get("/health", () => HttpResponse.error()),
    )
    renderWithProviders(<ConnectionStatus />)
    await waitFor(() => {
      expect(screen.getByText("Disconnected")).toBeInTheDocument()
    })
  })

  it('shows "Disconnected" when both status and redis are unhealthy', async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json({ status: "error", redis: "disconnected" }),
      ),
    )
    renderWithProviders(<ConnectionStatus />)
    await waitFor(() => {
      expect(screen.getByText("Disconnected")).toBeInTheDocument()
    })
  })

  it('shows "Checking..." initially while loading', () => {
    server.use(
      http.get("/health", () => new Promise(() => {})),
    )
    renderWithProviders(<ConnectionStatus />)
    expect(screen.getByText("Checking...")).toBeInTheDocument()
  })

  it("shows offline banner when disconnected", async () => {
    server.use(
      http.get("/health", () => HttpResponse.error()),
    )
    renderWithProviders(<ConnectionStatus />)
    await waitFor(() => {
      expect(screen.getByText(/You are offline/)).toBeInTheDocument()
    })
  })

  it("does not show offline banner when connected", async () => {
    renderWithProviders(<ConnectionStatus />)
    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument()
    })
    expect(screen.queryByText(/You are offline/)).not.toBeInTheDocument()
  })
})

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <OfflineQueueProvider>{children}</OfflineQueueProvider>
      </QueryClientProvider>
    )
  }
}

describe("useOfflineQueue", () => {
  it("starts online by default", () => {
    const { result } = renderHook(() => useOfflineQueue(), {
      wrapper: createWrapper(),
    })
    expect(result.current.isOnline).toBe(true)
    expect(result.current.pendingMutations).toEqual([])
  })

  it("queues mutation when offline", async () => {
    server.use(
      http.get("/health", () => HttpResponse.error()),
    )

    const { result } = renderHook(() => useOfflineQueue(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isOnline).toBe(false)
    })

    const mockMutation = vi.fn().mockResolvedValue(undefined)

    act(() => {
      result.current.queueMutation({
        mutationFn: mockMutation,
        description: "Test mutation",
      })
    })

    expect(result.current.pendingMutations).toHaveLength(1)
    expect(result.current.pendingMutations[0].description).toBe("Test mutation")
    expect(mockMutation).not.toHaveBeenCalled()
  })

  it("executes mutation immediately when online", () => {
    const mockMutation = vi.fn().mockResolvedValue(undefined)

    const { result } = renderHook(() => useOfflineQueue(), {
      wrapper: createWrapper(),
    })

    act(() => {
      result.current.queueMutation({
        mutationFn: mockMutation,
        description: "Test mutation",
      })
    })

    expect(mockMutation).toHaveBeenCalledTimes(1)
    expect(result.current.pendingMutations).toHaveLength(0)
  })

  it("removes mutation from queue", async () => {
    server.use(
      http.get("/health", () => HttpResponse.error()),
    )

    const { result } = renderHook(() => useOfflineQueue(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isOnline).toBe(false)
    })

    let mutationId = ""
    act(() => {
      mutationId = result.current.queueMutation({
        mutationFn: vi.fn().mockResolvedValue(undefined),
        description: "Test mutation",
      })
    })

    expect(result.current.pendingMutations).toHaveLength(1)

    act(() => {
      result.current.removeMutation(mutationId)
    })

    expect(result.current.pendingMutations).toHaveLength(0)
  })
})
