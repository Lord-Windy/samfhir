import { useParams } from 'react-router'

export function DashboardPage() {
  const { id } = useParams<{ id: string }>()
  
  return (
    <div>
      <h1 className="text-3xl font-bold">Patient Dashboard</h1>
      <p className="mt-2 text-muted-foreground">
        Patient ID: {id}
      </p>
    </div>
  )
}
