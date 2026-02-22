import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import {
  searchPatients,
  getPatient,
  getPatientSummary,
  getConditions,
  getObservations,
  getMedications,
  getAllergies,
  createObservation,
  createCondition,
  getCacheStats,
  flushCache,
  getHealth,
} from "./endpoints"
import type { CreateObservationRequest, CreateConditionRequest } from "@/types/api"

describe("API endpoints", () => {
  it("searchPatients() calls /api/v1/patients without params", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients", ({ request }) => {
        const url = new URL(request.url)
        handler(url.pathname, url.search)
        return HttpResponse.json([])
      }),
    )
    await searchPatients()
    expect(handler).toHaveBeenCalledWith("/api/v1/patients", "")
  })

  it("searchPatients(name) encodes the name parameter", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients", ({ request }) => {
        const url = new URL(request.url)
        handler(url.searchParams.get("name"))
        return HttpResponse.json([])
      }),
    )
    await searchPatients("O'Brien")
    expect(handler).toHaveBeenCalledWith("O'Brien")
  })

  it("getPatient() calls /api/v1/patients/:id", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients/:id", ({ params }) => {
        handler(params.id)
        return HttpResponse.json({ id: params.id })
      }),
    )
    await getPatient("abc-123")
    expect(handler).toHaveBeenCalledWith("abc-123")
  })

  it("getPatientSummary() calls /api/v1/patients/:id/summary", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients/:id/summary", ({ params }) => {
        handler(params.id)
        return HttpResponse.json({
          patient: {},
          active_conditions: [],
          recent_observations: [],
          active_medications: [],
          allergies: [],
        })
      }),
    )
    await getPatientSummary("xyz-456")
    expect(handler).toHaveBeenCalledWith("xyz-456")
  })

  it("getConditions() calls /api/v1/patients/:id/conditions", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients/:id/conditions", ({ params }) => {
        handler(params.id)
        return HttpResponse.json([])
      }),
    )
    await getConditions("123")
    expect(handler).toHaveBeenCalledWith("123")
  })

  it("getObservations() calls /api/v1/patients/:id/observations", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients/:id/observations", ({ params }) => {
        handler(params.id)
        return HttpResponse.json([])
      }),
    )
    await getObservations("123")
    expect(handler).toHaveBeenCalledWith("123")
  })

  it("getMedications() calls /api/v1/patients/:id/medications", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients/:id/medications", ({ params }) => {
        handler(params.id)
        return HttpResponse.json([])
      }),
    )
    await getMedications("123")
    expect(handler).toHaveBeenCalledWith("123")
  })

  it("getAllergies() calls /api/v1/patients/:id/allergies", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/patients/:id/allergies", ({ params }) => {
        handler(params.id)
        return HttpResponse.json([])
      }),
    )
    await getAllergies("123")
    expect(handler).toHaveBeenCalledWith("123")
  })

  it("createObservation() POSTs to /api/v1/observations", async () => {
    const handler = vi.fn()
    server.use(
      http.post("/api/v1/observations", async ({ request }) => {
        handler(await request.json())
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const data: CreateObservationRequest = {
      patient_id: "123",
      code: "8480-6",
      display: "BP",
      value: "120",
    }
    await createObservation(data)
    expect(handler).toHaveBeenCalledWith(data)
  })

  it("createCondition() POSTs to /api/v1/conditions", async () => {
    const handler = vi.fn()
    server.use(
      http.post("/api/v1/conditions", async ({ request }) => {
        handler(await request.json())
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const data: CreateConditionRequest = {
      patient_id: "123",
      code: "73211009",
      display: "Diabetes",
    }
    await createCondition(data)
    expect(handler).toHaveBeenCalledWith(data)
  })

  it("getCacheStats() calls /api/v1/cache/stats", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/api/v1/cache/stats", () => {
        handler()
        return HttpResponse.json({ hits: 0, misses: 0 })
      }),
    )
    await getCacheStats()
    expect(handler).toHaveBeenCalledOnce()
  })

  it("flushCache() DELETEs /api/v1/cache", async () => {
    const handler = vi.fn()
    server.use(
      http.delete("/api/v1/cache", () => {
        handler()
        return HttpResponse.json({ status: "flushed" })
      }),
    )
    await flushCache()
    expect(handler).toHaveBeenCalledOnce()
  })

  it("getHealth() calls /health", async () => {
    const handler = vi.fn()
    server.use(
      http.get("/health", () => {
        handler()
        return HttpResponse.json({ status: "ok", redis: "connected" })
      }),
    )
    await getHealth()
    expect(handler).toHaveBeenCalledOnce()
  })
})
