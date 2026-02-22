/** ISO 8601 date string (YYYY-MM-DD) */
export type ISODateString = string;

// ── Requests ──────────────────────────────────────────────────────────

export interface CreateObservationRequest {
  patient_id: string;
  code: string;
  display: string;
  value: string;
  unit?: string;
  effective_date?: ISODateString;
}

export interface CreateConditionRequest {
  patient_id: string;
  code: string;
  display: string;
  clinical_status?: string; // default "active"
  onset_date?: ISODateString;
}

// ── Responses ─────────────────────────────────────────────────────────

export interface PatientResponse {
  id: string;
  family_name: string;
  given_name: string;
  birth_date: ISODateString;
  gender: string;
}

export interface ConditionResponse {
  id: string;
  code: string;
  display: string;
  clinical_status: string;
  onset_date: ISODateString | null;
}

export interface ObservationResponse {
  id: string;
  code: string;
  display: string;
  value: string;
  unit: string | null;
  effective_date: ISODateString | null;
}

export interface MedicationResponse {
  id: string;
  code: string;
  display: string;
  status: string;
  authored_on: ISODateString | null;
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

export interface ReadinessResponse {
  ready: boolean;
}

// ── Errors ────────────────────────────────────────────────────────────

export interface ApiErrorBody {
  error: string;
  detail?: string | ValidationErrorDetail[];
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
