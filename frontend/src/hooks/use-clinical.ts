import { useQuery } from "@tanstack/react-query"
import {
  getAllergies,
  getConditions,
  getMedications,
  getObservations,
} from "@/api/endpoints"
import { queryKeys } from "./query-keys"

export function useConditions(patientId: string) {
  return useQuery({
    queryKey: queryKeys.conditions(patientId),
    queryFn: () => getConditions(patientId),
    enabled: !!patientId,
  })
}

export function useObservations(patientId: string) {
  return useQuery({
    queryKey: queryKeys.observations(patientId),
    queryFn: () => getObservations(patientId),
    enabled: !!patientId,
  })
}

export function useMedications(patientId: string) {
  return useQuery({
    queryKey: queryKeys.medications(patientId),
    queryFn: () => getMedications(patientId),
    enabled: !!patientId,
  })
}

export function useAllergies(patientId: string) {
  return useQuery({
    queryKey: queryKeys.allergies(patientId),
    queryFn: () => getAllergies(patientId),
    enabled: !!patientId,
  })
}
