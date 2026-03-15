import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatRelativeTime } from "@/lib/utils"
import type { PatientResponse } from "@/types/api"

interface PatientDemographicsProps {
  patient: PatientResponse
  lastUpdated?: number
}

export function PatientDemographics({ patient, lastUpdated }: PatientDemographicsProps) {
  const formattedDob = new Date(patient.birth_date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })

  const genderDisplay = patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <CardTitle>
          {patient.given_name} {patient.family_name}
        </CardTitle>
        {lastUpdated && (
          <span className="text-xs text-muted-foreground">
            {formatRelativeTime(lastUpdated)}
          </span>
        )}
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-muted-foreground">Date of Birth</dt>
            <dd className="font-medium">{formattedDob}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Gender</dt>
            <dd className="font-medium">{genderDisplay}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Patient ID</dt>
            <dd className="font-mono text-xs">{patient.id}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  )
}
