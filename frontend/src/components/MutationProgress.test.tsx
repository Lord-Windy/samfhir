import { screen, waitFor } from "@testing-library/react"
import { render } from "@testing-library/react"
import { vi } from "vitest"
import { MutationProgress } from "./MutationProgress"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = createQueryClient()
  return {
    ...render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    ),
    queryClient,
  }
}

describe("MutationProgress", () => {
  const defaultProps = {
    isPending: false,
    isSuccess: false,
    isError: false,
    onComplete: vi.fn(),
  }

  it("does not render when idle", () => {
    const { container } = renderWithQueryClient(
      <MutationProgress {...defaultProps} />
    )
    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument()
  })

  it("renders saving phase when pending", () => {
    renderWithQueryClient(
      <MutationProgress {...defaultProps} isPending={true} />
    )
    expect(screen.getByText("Saving...")).toBeInTheDocument()
    expect(screen.getByRole("dialog")).toBeInTheDocument()
  })

  it("shows saved phase after success", async () => {
    const { rerender } = renderWithQueryClient(
      <MutationProgress {...defaultProps} isPending={true} />
    )

    expect(screen.getByText("Saving...")).toBeInTheDocument()

    rerender(
      <QueryClientProvider client={createQueryClient()}>
        <MutationProgress
          {...defaultProps}
          isPending={false}
          isSuccess={true}
        />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText(/Saved to server/)).toBeInTheDocument()
    })
  })

  it("shows error phase on error", async () => {
    renderWithQueryClient(
      <MutationProgress
        {...defaultProps}
        isPending={true}
        isError={true}
        errorMessage="Something went wrong"
      />
    )

    await waitFor(() => {
      expect(screen.getByText("Something went wrong")).toBeInTheDocument()
    })
  })

  it("calls onComplete after complete phase", async () => {
    const onComplete = vi.fn()

    const { rerender } = renderWithQueryClient(
      <MutationProgress {...defaultProps} onComplete={onComplete} isPending={true} />
    )

    rerender(
      <QueryClientProvider client={createQueryClient()}>
        <MutationProgress
          {...defaultProps}
          onComplete={onComplete}
          isPending={false}
          isSuccess={true}
        />
      </QueryClientProvider>
    )

    await waitFor(
      () => {
        expect(onComplete).toHaveBeenCalled()
      },
      { timeout: 4000 }
    )
  })

  it("has correct accessibility attributes", () => {
    renderWithQueryClient(
      <MutationProgress {...defaultProps} isPending={true} />
    )
    const dialog = screen.getByRole("dialog")
    expect(dialog).toHaveAttribute("aria-modal", "true")
    expect(dialog).toHaveAttribute("aria-labelledby", "mutation-progress-title")
  })

  it("has data-phase attribute for testing", () => {
    renderWithQueryClient(
      <MutationProgress {...defaultProps} isPending={true} />
    )
    const title = screen.getByText("Saving...")
    expect(title).toHaveAttribute("data-phase", "saving")
  })
})
