import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createCondition, createObservation } from "@/api/endpoints"
import { queryKeys } from "./query-keys"
import type { CreateObservationRequest, ObservationResponse } from "@/types/api"

function generateTempId(): string {
  return `temp-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function useCreateObservation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createObservation,
    onMutate: async (variables: CreateObservationRequest) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.observations(variables.patient_id),
      })

      const previousObservations = queryClient.getQueryData<ObservationResponse[]>(
        queryKeys.observations(variables.patient_id),
      )

      const optimisticObservation: ObservationResponse = {
        id: generateTempId(),
        code: variables.code,
        display: variables.display,
        value: variables.value,
        unit: variables.unit ?? null,
        effective_date: variables.effective_date ?? null,
      }

      queryClient.setQueryData<ObservationResponse[]>(
        queryKeys.observations(variables.patient_id),
        (old) => (old ? [...old, optimisticObservation] : [optimisticObservation]),
      )

      return { previousObservations }
    },
    onError: (_err, variables, context) => {
      if (context?.previousObservations) {
        queryClient.setQueryData(
          queryKeys.observations(variables.patient_id),
          context.previousObservations,
        )
      }
    },
    onSettled: (_data, _error, variables) => {
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
