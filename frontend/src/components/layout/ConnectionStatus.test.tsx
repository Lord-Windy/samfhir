import { screen, waitFor } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import { renderWithProviders } from "@/test-utils"
import { ConnectionStatus } from "./ConnectionStatus"

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
})
