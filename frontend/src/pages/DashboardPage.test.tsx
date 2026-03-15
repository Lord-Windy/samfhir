import { screen, waitFor, fireEvent } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import { renderWithProviders } from "@/test-utils"
import { DashboardPage } from "./DashboardPage"
import { Route, Routes } from "react-router"

function renderDashboard(patientId: string) {
  return renderWithProviders(
    <Routes>
      <Route path="/patients/:id" element={<DashboardPage />} />
    </Routes>,
    { initialEntries: [`/patients/${patientId}`] },
  )
}

describe("DashboardPage", () => {
  it("renders patient name after loading", async () => {
    renderDashboard("592912")
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("John Smith")
    })
  })

  it("renders clinical tabs with counts", async () => {
    renderDashboard("592912")
    await waitFor(() => {
      expect(screen.getByText("Conditions (1)")).toBeInTheDocument()
    })
    expect(screen.getByText("Observations (1)")).toBeInTheDocument()
    expect(screen.getByText("Medications (1)")).toBeInTheDocument()
    expect(screen.getByText("Allergies (1)")).toBeInTheDocument()
  })

  it("renders patient demographics", async () => {
    renderDashboard("592912")
    await waitFor(() => {
      expect(screen.getByText("592912")).toBeInTheDocument()
    })
  })

  it('shows "Patient Not Found" on 404', async () => {
    server.use(
      http.get("/api/v1/patients/:id/summary", () =>
        HttpResponse.json(
          { error: "Not found", detail: "No patient" },
          { status: 404 },
        ),
      ),
    )
    renderDashboard("nonexistent")
    await waitFor(() => {
      expect(screen.getByText("Patient Not Found")).toBeInTheDocument()
    })
  })

  it('shows "Service Unavailable" on 502', async () => {
    server.use(
      http.get("/api/v1/patients/:id/summary", () =>
        HttpResponse.json(
          { error: "Bad Gateway" },
          { status: 502 },
        ),
      ),
    )
    renderDashboard("592912")
    await waitFor(() => {
      expect(screen.getByText("Service Unavailable")).toBeInTheDocument()
    })
  })

  it("shows generic error on unexpected failure", async () => {
    server.use(
      http.get("/api/v1/patients/:id/summary", () =>
        HttpResponse.json(
          { error: "Something broke" },
          { status: 418 },
        ),
      ),
    )
    renderDashboard("592912")
    await waitFor(() => {
      expect(
        screen.getByText(/unexpected error/i),
      ).toBeInTheDocument()
    })
  })

  it("renders refresh button and triggers refetch on click", async () => {
    renderDashboard("592912")
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("John Smith")
    })

    const refreshButton = screen.getByRole("button", { name: /refresh patient data/i })
    expect(refreshButton).toBeInTheDocument()

    let fetchCount = 0
    server.use(
      http.get("/api/v1/patients/:id/summary", () => {
        fetchCount++
        return HttpResponse.json({
          patient: {
            id: "592912",
            given_name: "John",
            family_name: "Smith",
            birth_date: "1990-01-01",
            gender: "male",
          },
          active_conditions: [],
          recent_observations: [],
          active_medications: [],
          allergies: [],
        })
      }),
    )

    fireEvent.click(refreshButton)
    await waitFor(() => {
      expect(fetchCount).toBe(1)
    })
  })
})
