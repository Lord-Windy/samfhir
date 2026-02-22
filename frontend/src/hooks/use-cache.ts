import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { flushCache, getCacheStats } from "@/api/endpoints"
import { queryKeys } from "./query-keys"

export function useCacheStats() {
  return useQuery({
    queryKey: queryKeys.cache,
    queryFn: getCacheStats,
  })
}

export function useFlushCache() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: flushCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cache })
    },
  })
}
