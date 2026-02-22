import { useParams, Link } from "react-router"
import { Button } from "@/components/ui/button"

export function DashboardPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Patient Dashboard</h1>
        <Button asChild>
          <Link to={`/patients/${id}/observations/new`}>Add Observation</Link>
        </Button>
      </div>
      <p className="mt-2 text-muted-foreground">
        Patient ID: {id}
      </p>
    </div>
  )
}
