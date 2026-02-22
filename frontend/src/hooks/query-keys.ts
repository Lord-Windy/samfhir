export const queryKeys = {
  patients: {
    all: ["patients"] as const,
    search: (name?: string) => ["patients", "search", name] as const,
    detail: (id: string) => ["patients", id] as const,
    summary: (id: string) => ["patients", id, "summary"] as const,
  },
  conditions: (patientId: string) =>
    ["patients", patientId, "conditions"] as const,
  observations: (patientId: string) =>
    ["patients", patientId, "observations"] as const,
  medications: (patientId: string) =>
    ["patients", patientId, "medications"] as const,
  allergies: (patientId: string) =>
    ["patients", patientId, "allergies"] as const,
  cache: ["cache", "stats"] as const,
  health: ["health"] as const,
}
