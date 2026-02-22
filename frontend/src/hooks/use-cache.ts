import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { flushCache, getCacheStats } from "@/api/endpoints"
import { queryKeys } from "./query-keys"

export function useCacheStats(options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.cache,
    queryFn: getCacheStats,
    refetchInterval: options?.refetchInterval,
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
