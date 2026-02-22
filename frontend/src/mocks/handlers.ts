import { http, HttpResponse } from "msw"
import type {
  PatientResponse,
  PatientSummaryResponse,
  ConditionResponse,
  ObservationResponse,
  MedicationResponse,
  AllergyResponse,
  CacheStatsResponse,
  HealthResponse,
} from "@/types/api"

// ── Fixtures ────────────────────────────────────────────────────────

export const mockPatient: PatientResponse = {
  id: "592912",
  family_name: "Smith",
  given_name: "John",
  birth_date: "1990-01-15",
  gender: "male",
}

export const mockPatient2: PatientResponse = {
  id: "592913",
  family_name: "Smith",
  given_name: "Jane",
  birth_date: "1985-06-20",
  gender: "female",
}

export const mockCondition: ConditionResponse = {
  id: "cond-1",
  code: "73211009",
  display: "Diabetes mellitus",
  clinical_status: "active",
  onset_date: "2020-03-15",
}

export const mockObservation: ObservationResponse = {
  id: "obs-1",
  code: "8480-6",
  display: "Systolic blood pressure",
  value: "120",
  unit: "mmHg",
  effective_date: "2024-01-10",
}

export const mockMedication: MedicationResponse = {
  id: "med-1",
  code: "860975",
  display: "Metformin 500mg",
  status: "active",
  authored_on: "2023-06-01",
}

export const mockAllergy: AllergyResponse = {
  id: "allergy-1",
  code: "70618",
  display: "Penicillin",
  clinical_status: "active",
  criticality: "high",
}

export const mockSummary: PatientSummaryResponse = {
  patient: mockPatient,
  active_conditions: [mockCondition],
  recent_observations: [mockObservation],
  active_medications: [mockMedication],
  allergies: [mockAllergy],
}

export const mockHealth: HealthResponse = {
  status: "ok",
  redis: "connected",
}

export const mockCacheStats: CacheStatsResponse = {
  hits: 42,
  misses: 7,
}

// ── Handlers ────────────────────────────────────────────────────────

export const handlers = [
  // Patient search
  http.get("/api/v1/patients", ({ request }) => {
    const url = new URL(request.url)
    const name = url.searchParams.get("name")
    if (name) {
      const filtered = [mockPatient, mockPatient2].filter(
        (p) =>
          p.family_name.toLowerCase().includes(name.toLowerCase()) ||
          p.given_name.toLowerCase().includes(name.toLowerCase()),
      )
      return HttpResponse.json(filtered)
    }
    return HttpResponse.json([mockPatient, mockPatient2])
  }),

  // Patient by ID
  http.get("/api/v1/patients/:id/summary", ({ params }) => {
    const { id } = params
    if (id === mockPatient.id) return HttpResponse.json(mockSummary)
    return HttpResponse.json(
      { error: "Patient not found", detail: `No patient with id ${id}` },
      { status: 404 },
    )
  }),

  http.get("/api/v1/patients/:id/conditions", () =>
    HttpResponse.json([mockCondition]),
  ),
  http.get("/api/v1/patients/:id/observations", () =>
    HttpResponse.json([mockObservation]),
  ),
  http.get("/api/v1/patients/:id/medications", () =>
    HttpResponse.json([mockMedication]),
  ),
  http.get("/api/v1/patients/:id/allergies", () =>
    HttpResponse.json([mockAllergy]),
  ),

  http.get("/api/v1/patients/:id", ({ params }) => {
    const { id } = params
    if (id === mockPatient.id) return HttpResponse.json(mockPatient)
    return HttpResponse.json(
      { error: "Patient not found", detail: `No patient with id ${id}` },
      { status: 404 },
    )
  }),

  // Write endpoints
  http.post("/api/v1/observations", () =>
    HttpResponse.json(mockObservation, { status: 201 }),
  ),
  http.post("/api/v1/conditions", () =>
    HttpResponse.json(mockCondition, { status: 201 }),
  ),

  // Cache
  http.get("/api/v1/cache/stats", () =>
    HttpResponse.json(mockCacheStats),
  ),
  http.delete("/api/v1/cache", () =>
    HttpResponse.json({ status: "flushed" }),
  ),

  // Health
  http.get("/health", () => HttpResponse.json(mockHealth)),
]
