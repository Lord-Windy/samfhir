import { waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render } from "@testing-library/react"
import { GlobalLoadingBar } from "./GlobalLoadingBar"

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

    const mutation = queryClient.getMutationCache().build(queryClient, {
      mutationFn: () => new Promise(() => {}),
    })

    mutation.execute(undefined)

    await waitFor(() => {
      expect(container.querySelector(".animate-progress")).toBeInTheDocument()
    })
  })
})
