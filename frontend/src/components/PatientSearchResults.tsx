import type { PatientResponse } from "@/types/api"
import { PatientCard } from "./PatientCard"

interface PatientSearchResultsProps {
  patients: PatientResponse[]
}

export function PatientSearchResults({ patients }: PatientSearchResultsProps) {
  if (patients.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No patients found.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {patients.map((patient) => (
        <PatientCard key={patient.id} patient={patient} />
      ))}
    </div>
  )
}
