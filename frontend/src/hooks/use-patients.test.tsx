import { renderHook, waitFor } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import { useSearchPatients, usePatient, usePatientSummary } from "./use-patients"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe("useSearchPatients", () => {
  it("does not fetch when name is undefined", () => {
    const { result } = renderHook(() => useSearchPatients(undefined), {
      wrapper: createWrapper(),
    })
    expect(result.current.isFetching).toBe(false)
    expect(result.current.data).toBeUndefined()
  })

  it("fetches patients matching name", async () => {
    const { result } = renderHook(() => useSearchPatients("Smith"), {
      wrapper: createWrapper(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.[0].family_name).toBe("Smith")
  })

  it("returns error when API fails", async () => {
    server.use(
      http.get("/api/v1/patients", () =>
        HttpResponse.json({ error: "Server error" }, { status: 500 }),
      ),
    )
    const { result } = renderHook(() => useSearchPatients("Smith"), {
      wrapper: createWrapper(),
    })
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toBeDefined()
  })
})

describe("usePatient", () => {
  it("does not fetch when patientId is empty string", () => {
    const { result } = renderHook(() => usePatient(""), {
      wrapper: createWrapper(),
    })
    expect(result.current.isFetching).toBe(false)
  })

  it("fetches patient by ID", async () => {
    const { result } = renderHook(() => usePatient("592912"), {
      wrapper: createWrapper(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.id).toBe("592912")
  })
})

describe("usePatientSummary", () => {
  it("fetches patient summary", async () => {
    const { result } = renderHook(() => usePatientSummary("592912"), {
      wrapper: createWrapper(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.patient.id).toBe("592912")
    expect(result.current.data?.active_conditions).toHaveLength(1)
  })
})
