import { useQuery, useQueryClient } from "@tanstack/react-query"
import { getPatient, getPatientSummary, searchPatients } from "@/api/endpoints"
import { queryKeys } from "./query-keys"

export function useSearchPatients(name?: string) {
  return useQuery({
    queryKey: queryKeys.patients.search(name),
    queryFn: () => searchPatients(name),
    enabled: name !== undefined,
  })
}

export function usePatient(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.detail(patientId),
    queryFn: () => getPatient(patientId),
    enabled: !!patientId,
  })
}

export function usePatientSummary(patientId: string) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: queryKeys.patients.summary(patientId),
    queryFn: () => getPatientSummary(patientId),
    enabled: !!patientId,
  })
  const refresh = () =>
    queryClient.fetchQuery({
      queryKey: queryKeys.patients.summary(patientId),
      queryFn: () => getPatientSummary(patientId, true),
    })
  return { ...query, refresh }
}
