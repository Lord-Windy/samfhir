import { toast } from "sonner"
import { useCacheStats, useFlushCache } from "@/hooks/use-cache"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export function CacheStatsPage() {
  const { data: stats, isPending, isError } = useCacheStats({ refetchInterval: 10000 })
  const flushCache = useFlushCache()

  const hits = stats?.hits ?? 0
  const misses = stats?.misses ?? 0
  const total = hits + misses
  const hitRate = total > 0 ? ((hits / total) * 100).toFixed(1) : "0.0"

  return (
    <div>
      <h2 className="text-xl font-semibold">Cache Statistics</h2>

      {isError && (
        <p className="mt-4 text-sm text-destructive">
          Failed to load cache statistics.
        </p>
      )}

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        {[
          { title: "Hit Count", value: hits },
          { title: "Miss Count", value: misses },
          { title: "Hit Rate", value: `${hitRate}%` },
        ].map((stat) => (
          <Card key={stat.title}>
            <CardHeader>
              <CardTitle>{stat.title}</CardTitle>
            </CardHeader>
            <CardContent>
              {isPending ? (
                <Skeleton className="h-9 w-20" />
              ) : (
                <p className="text-3xl font-bold">{stat.value}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6">
        <Button
          variant="destructive"
          onClick={() =>
            flushCache.mutate(undefined, {
              onSuccess: () => toast.success("Cache flushed"),
              onError: () => toast.error("Failed to flush cache"),
            })
          }
          disabled={flushCache.isPending}
        >
          {flushCache.isPending ? "Flushing..." : "Flush Cache"}
        </Button>
      </div>
    </div>
  )
}
