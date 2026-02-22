import { del, get, post } from "./client";
import type {
  AllergyResponse,
  CacheStatsResponse,
  ConditionResponse,
  CreateConditionRequest,
  CreateObservationRequest,
  HealthResponse,
  MedicationResponse,
  ObservationResponse,
  PatientResponse,
  PatientSummaryResponse,
} from "@/types/api";

// ── Patients ─────────────────────────────────────────────────────────

export function searchPatients(name?: string): Promise<PatientResponse[]> {
  const params = name ? `?name=${encodeURIComponent(name)}` : "";
  return get<PatientResponse[]>(`/api/v1/patients${params}`);
}

export function getPatient(patientId: string): Promise<PatientResponse> {
  return get<PatientResponse>(`/api/v1/patients/${patientId}`);
}

export function getPatientSummary(
  patientId: string,
): Promise<PatientSummaryResponse> {
  return get<PatientSummaryResponse>(
    `/api/v1/patients/${patientId}/summary`,
  );
}

export function getConditions(
  patientId: string,
): Promise<ConditionResponse[]> {
  return get<ConditionResponse[]>(
    `/api/v1/patients/${patientId}/conditions`,
  );
}

export function getObservations(
  patientId: string,
): Promise<ObservationResponse[]> {
  return get<ObservationResponse[]>(
    `/api/v1/patients/${patientId}/observations`,
  );
}

export function getMedications(
  patientId: string,
): Promise<MedicationResponse[]> {
  return get<MedicationResponse[]>(
    `/api/v1/patients/${patientId}/medications`,
  );
}

export function getAllergies(
  patientId: string,
): Promise<AllergyResponse[]> {
  return get<AllergyResponse[]>(
    `/api/v1/patients/${patientId}/allergies`,
  );
}

// ── Write ────────────────────────────────────────────────────────────

export function createObservation(
  data: CreateObservationRequest,
): Promise<ObservationResponse> {
  return post<ObservationResponse>("/api/v1/observations", data);
}

export function createCondition(
  data: CreateConditionRequest,
): Promise<ConditionResponse> {
  return post<ConditionResponse>("/api/v1/conditions", data);
}

// ── Cache ────────────────────────────────────────────────────────────

export function getCacheStats(): Promise<CacheStatsResponse> {
  return get<CacheStatsResponse>("/api/v1/cache/stats");
}

export function flushCache(): Promise<{ status: string }> {
  return del<{ status: string }>("/api/v1/cache");
}

// ── Health ───────────────────────────────────────────────────────────

export function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/health");
}
