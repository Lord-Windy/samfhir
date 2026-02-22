import { useCacheStats, useFlushCache } from "@/hooks/use-cache"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function CacheStatsPage() {
  const { data: stats } = useCacheStats({ refetchInterval: 10000 })
  const flushCache = useFlushCache()

  const hits = stats?.hits ?? 0
  const misses = stats?.misses ?? 0
  const total = hits + misses
  const hitRate = total > 0 ? ((hits / total) * 100).toFixed(1) : "0.0"

  return (
    <div>
      <h2 className="text-xl font-semibold">Cache Statistics</h2>
      <p className="mt-2 text-muted-foreground">View cache performance metrics...</p>

      <div className="mt-6 grid grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Hit Count</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{hits}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Miss Count</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{misses}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hit Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{hitRate}%</p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6">
        <Button
          variant="destructive"
          onClick={() => flushCache.mutate()}
          disabled={flushCache.isPending}
        >
          {flushCache.isPending ? "Flushing..." : "Flush Cache"}
        </Button>
      </div>
    </div>
  )
}
