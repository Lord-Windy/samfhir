// ── Requests ──────────────────────────────────────────────────────────

export interface CreateObservationRequest {
  patient_id: string;
  code: string;
  display: string;
  value: string;
  unit?: string;
  effective_date?: string;
}

export interface CreateConditionRequest {
  patient_id: string;
  code: string;
  display: string;
  clinical_status?: string; // default "active"
  onset_date?: string;
}

// ── Responses ─────────────────────────────────────────────────────────

export interface PatientResponse {
  id: string;
  family_name: string;
  given_name: string;
  birth_date: string;
  gender: string;
}

export interface ConditionResponse {
  id: string;
  code: string;
  display: string;
  clinical_status: string;
  onset_date: string | null;
}

export interface ObservationResponse {
  id: string;
  code: string;
  display: string;
  value: string;
  unit: string | null;
  effective_date: string | null;
}

export interface MedicationResponse {
  id: string;
  code: string;
  display: string;
  status: string;
  authored_on: string | null;
}

export interface AllergyResponse {
  id: string;
  code: string;
  display: string;
  clinical_status: string;
  criticality: string | null;
}

export interface PatientSummaryResponse {
  patient: PatientResponse;
  active_conditions: ConditionResponse[];
  recent_observations: ObservationResponse[];
  active_medications: MedicationResponse[];
  allergies: AllergyResponse[];
}

export interface CacheStatsResponse {
  hits: number;
  misses: number;
}

export interface HealthResponse {
  status: string;
  redis: string;
}

// ── Errors ────────────────────────────────────────────────────────────

export interface ApiErrorBody {
  error: string;
  detail?: string;
  patient_id?: string;
}

export interface ValidationErrorDetail {
  type: string;
  loc: (string | number)[];
  msg: string;
  input: unknown;
}

export interface ValidationErrorBody {
  detail: ValidationErrorDetail[];
}
