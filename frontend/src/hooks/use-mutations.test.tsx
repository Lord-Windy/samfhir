import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import { useCreateObservation, useCreateCondition } from "./use-mutations"
import { queryKeys } from "./query-keys"
import type { ObservationResponse, CreateObservationRequest } from "@/types/api"

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

describe("useCreateObservation", () => {
  const patientId = "patient-123"
  const existingObservation: ObservationResponse = {
    id: "obs-1",
    code: "8480-6",
    display: "Systolic Blood Pressure",
    value: "120",
    unit: "mmHg",
    effective_date: "2024-01-15",
  }

  const newObservationRequest: CreateObservationRequest = {
    patient_id: patientId,
    code: "8462-4",
    display: "Diastolic Blood Pressure",
    value: "80",
    unit: "mmHg",
    effective_date: "2024-01-20",
  }

  const createdObservation: ObservationResponse = {
    id: "obs-2",
    code: "8462-4",
    display: "Diastolic Blood Pressure",
    value: "80",
    unit: "mmHg",
    effective_date: "2024-01-20",
  }

  it("optimistically adds observation to cache before server responds", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    })
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    queryClient.setQueryData(queryKeys.observations(patientId), [existingObservation])

    server.use(
      http.post("/api/v1/observations", async () => {
        await new Promise((r) => setTimeout(r, 100))
        return HttpResponse.json(createdObservation, { status: 201 })
      }),
    )

    const { result } = renderHook(() => useCreateObservation(), { wrapper })

    result.current.mutate(newObservationRequest)

    await waitFor(() => {
      const observations = queryClient.getQueryData<ObservationResponse[]>(
        queryKeys.observations(patientId),
      )
      expect(observations).toHaveLength(2)
    })

    const observations = queryClient.getQueryData<ObservationResponse[]>(
      queryKeys.observations(patientId),
    )
    const optimisticObs = observations!.find((o) => o.id.startsWith("temp-"))
    expect(optimisticObs).toMatchObject({
      code: newObservationRequest.code,
      display: newObservationRequest.display,
      value: newObservationRequest.value,
      unit: newObservationRequest.unit,
      effective_date: newObservationRequest.effective_date,
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })

  it("rolls back optimistic update on error", async () => {
    const queryClient = createQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    queryClient.setQueryData(queryKeys.observations(patientId), [existingObservation])

    server.use(
      http.post("/api/v1/observations", () => {
        return HttpResponse.json({ error: "Server error" }, { status: 500 })
      }),
    )

    const { result } = renderHook(() => useCreateObservation(), { wrapper })

    result.current.mutate(newObservationRequest)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    const observations = queryClient.getQueryData<ObservationResponse[]>(
      queryKeys.observations(patientId),
    )
    expect(observations).toEqual([existingObservation])
  })

  it("invalidates queries on success", async () => {
    const queryClient = createQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    server.use(
      http.post("/api/v1/observations", () => {
        return HttpResponse.json(createdObservation, { status: 201 })
      }),
    )

    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")

    const { result } = renderHook(() => useCreateObservation(), { wrapper })

    result.current.mutate(newObservationRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: queryKeys.observations(patientId),
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: queryKeys.patients.summary(patientId),
    })
  })
})

describe("useCreateCondition", () => {
  it("invalidates conditions and summary queries on success", async () => {
    const queryClient = createQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const patientId = "patient-123"

    server.use(
      http.post("/api/v1/conditions", () => {
        return HttpResponse.json(
          { id: "cond-1", code: "123", display: "Test", clinical_status: "active", onset_date: null },
          { status: 201 },
        )
      }),
    )

    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")

    const { result } = renderHook(() => useCreateCondition(), { wrapper })

    result.current.mutate({
      patient_id: patientId,
      code: "123",
      display: "Test Condition",
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: queryKeys.conditions(patientId),
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: queryKeys.patients.summary(patientId),
    })
  })
})
