import { Link } from "react-router"
import type { PatientResponse } from "@/types/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface PatientCardProps {
  patient: PatientResponse
}

export function PatientCard({ patient }: PatientCardProps) {
  return (
    <Link to={`/patients/${patient.id}`} className="block">
      <Card className="py-4 transition-colors hover:bg-accent/50">
        <CardContent className="flex items-center justify-between">
          <div className="flex flex-col gap-1">
            <span className="font-medium">
              {patient.given_name} {patient.family_name}
            </span>
            <span className="text-sm text-muted-foreground">
              Born {patient.birth_date}
            </span>
          </div>
          <Badge variant="outline">{patient.gender}</Badge>
        </CardContent>
      </Card>
    </Link>
  )
}
