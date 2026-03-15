import { waitFor, act } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render } from "@testing-library/react"
import { GlobalLoadingBar } from "./GlobalLoadingBar"
import { startRequest, endRequest, reset } from "@/api/request-timing"

function renderWithQueryClient() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <GlobalLoadingBar />
      </QueryClientProvider>,
    ),
    queryClient,
  }
}

describe("GlobalLoadingBar", () => {
  beforeEach(() => {
    reset()
  })

  it("does not render when no requests are pending", () => {
    const { container } = renderWithQueryClient()
    expect(container.firstChild).toBeNull()
  })

  it("renders when a query is fetching", async () => {
    const { container, queryClient } = renderWithQueryClient()

    queryClient.fetchQuery({
      queryKey: ["test"],
      queryFn: () => new Promise(() => {}),
    })

    await waitFor(() => {
      expect(container.querySelector(".animate-progress")).toBeInTheDocument()
    })
  })

  it("has accessibility attributes when visible", async () => {
    const { container, queryClient } = renderWithQueryClient()

    queryClient.fetchQuery({
      queryKey: ["test-a11y"],
      queryFn: () => new Promise(() => {}),
    })

    await waitFor(() => {
      const bar = container.querySelector('[role="progressbar"]')
      expect(bar).toBeInTheDocument()
      expect(bar).toHaveAttribute("aria-busy", "true")
      expect(bar).toHaveAttribute("aria-label", "Loading")
    })
  })

  it("renders when a mutation is in progress", async () => {
    const { container, queryClient } = renderWithQueryClient()

    queryClient.getMutationDefaults()

    const mutation = queryClient.getMutationCache().build(queryClient, {
      mutationFn: () => new Promise(() => {}),
    })

    mutation.execute()

    await waitFor(() => {
      expect(container.querySelector(".animate-progress")).toBeInTheDocument()
    })
  })
})

describe("GlobalLoadingBar elapsed time", () => {
  beforeEach(() => {
    reset()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("shows elapsed time for slow requests (>1s)", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <GlobalLoadingBar />
      </QueryClientProvider>,
    )

    queryClient.fetchQuery({
      queryKey: ["test-slow"],
      queryFn: () => new Promise(() => {}),
    })

    await act(async () => {
      vi.advanceTimersByTime(0)
    })

    const requestId = startRequest("/api/slow")
    
    await act(async () => {
      vi.advanceTimersByTime(1500)
    })

    const bar = container.querySelector('[role="progressbar"]')
    expect(bar).toHaveAttribute("aria-label", "Loading... (1.5s)")

    endRequest(requestId)
  })

  it("does not show elapsed time for fast requests (<1s)", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <GlobalLoadingBar />
      </QueryClientProvider>,
    )

    queryClient.fetchQuery({
      queryKey: ["test-fast"],
      queryFn: () => new Promise(() => {}),
    })

    await act(async () => {
      vi.advanceTimersByTime(0)
    })

    const requestId = startRequest("/api/fast")

    await act(async () => {
      vi.advanceTimersByTime(500)
    })

    const bar = container.querySelector('[role="progressbar"]')
    expect(bar).toHaveAttribute("aria-label", "Loading")

    endRequest(requestId)
  })
})
