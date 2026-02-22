import { useParams } from 'react-router'

export function ObservationFormPage() {
  const { id } = useParams<{ id: string }>()
  
  return (
    <div>
      <h1 className="text-3xl font-bold">New Observation</h1>
      <p className="mt-2 text-muted-foreground">
        Create observation for patient: {id}
      </p>
    </div>
  )
}
