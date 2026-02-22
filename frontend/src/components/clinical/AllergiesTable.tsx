import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import type { AllergyResponse } from "@/types/api"

interface AllergiesTableProps {
  allergies: AllergyResponse[]
}

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  active: "default",
  inactive: "outline",
  resolved: "secondary",
}

const criticalityVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  low: "secondary",
  medium: "default",
  high: "destructive",
  "unable-to-assess": "outline",
}

export function AllergiesTable({ allergies }: AllergiesTableProps) {
  if (allergies.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-8">
        No allergies found
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Allergy</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Criticality</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {allergies.map((allergy) => (
          <TableRow key={allergy.id}>
            <TableCell className="font-medium">{allergy.display}</TableCell>
            <TableCell>
              <Badge variant={statusVariant[allergy.clinical_status] || "outline"}>
                {allergy.clinical_status}
              </Badge>
            </TableCell>
            <TableCell>
              {allergy.criticality ? (
                <Badge variant={criticalityVariant[allergy.criticality] || "outline"}>
                  {allergy.criticality}
                </Badge>
              ) : (
                "—"
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
