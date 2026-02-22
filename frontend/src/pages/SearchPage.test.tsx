import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import { renderWithProviders } from "@/test-utils"
import { SearchPage } from "./SearchPage"

const mockNavigate = vi.fn()
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router")
  return { ...actual, useNavigate: () => mockNavigate }
})

describe("SearchPage", () => {
  it("renders search and lookup tabs", () => {
    renderWithProviders(<SearchPage />)
    expect(screen.getByText("Search by Name")).toBeInTheDocument()
    expect(screen.getByText("Lookup by ID")).toBeInTheDocument()
  })

  it("shows search results after typing a name", async () => {
    const user = userEvent.setup()
    renderWithProviders(<SearchPage />)

    const input = screen.getByPlaceholderText("e.g. Smith")
    await user.type(input, "Smith")

    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument()
    })
    expect(screen.getByText("Jane Smith")).toBeInTheDocument()
  })

  it("shows error alert when search fails", async () => {
    server.use(
      http.get("/api/v1/patients", () =>
        HttpResponse.json({ error: "Boom", detail: "Server error" }, { status: 500 }),
      ),
    )
    const user = userEvent.setup()
    renderWithProviders(<SearchPage />)

    await user.type(screen.getByPlaceholderText("e.g. Smith"), "test")
    await waitFor(() => {
      expect(screen.getByText("Search failed")).toBeInTheDocument()
    })
  })

  it("navigates to patient on ID lookup submit", async () => {
    const user = userEvent.setup()
    renderWithProviders(<SearchPage />)

    await user.click(screen.getByText("Lookup by ID"))
    const idInput = screen.getByPlaceholderText("e.g. 592912")
    await user.type(idInput, "592912")
    await user.click(screen.getByRole("button", { name: /view/i }))

    expect(mockNavigate).toHaveBeenCalledWith("/patients/592912")
  })
})
