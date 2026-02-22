import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import type { MedicationResponse } from "@/types/api"

interface MedicationsTableProps {
  medications: MedicationResponse[]
}

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  active: "default",
  completed: "secondary",
  stopped: "destructive",
  "on-hold": "outline",
}

export function MedicationsTable({ medications }: MedicationsTableProps) {
  if (medications.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-8">
        No medications found
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Medication</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Authored Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {medications.map((medication) => (
          <TableRow key={medication.id}>
            <TableCell className="font-medium">{medication.display}</TableCell>
            <TableCell>
              <Badge variant={statusVariant[medication.status] || "outline"}>
                {medication.status}
              </Badge>
            </TableCell>
            <TableCell>
              {medication.authored_on
                ? new Date(medication.authored_on).toLocaleDateString()
                : "—"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
