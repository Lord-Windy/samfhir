import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createCondition, createObservation } from "@/api/endpoints"
import { queryKeys } from "./query-keys"

export function useCreateObservation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createObservation,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.observations(variables.patient_id),
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.patients.summary(variables.patient_id),
      })
    },
  })
}

export function useCreateCondition() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createCondition,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.conditions(variables.patient_id),
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.patients.summary(variables.patient_id),
      })
    },
  })
}
