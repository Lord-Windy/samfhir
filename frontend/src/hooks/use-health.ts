import { useQuery } from "@tanstack/react-query"
import { getHealth } from "@/api/endpoints"
import { queryKeys } from "./query-keys"

export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    refetchInterval: 30_000,
  })
}
