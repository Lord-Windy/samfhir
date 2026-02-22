import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import type { ConditionResponse } from "@/types/api"

interface ConditionsTableProps {
  conditions: ConditionResponse[]
}

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  active: "default",
  resolved: "secondary",
  inactive: "outline",
}

export function ConditionsTable({ conditions }: ConditionsTableProps) {
  if (conditions.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-8">
        No conditions found
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Condition</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Onset Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {conditions.map((condition) => (
          <TableRow key={condition.id}>
            <TableCell className="font-medium">{condition.display}</TableCell>
            <TableCell>
              <Badge variant={statusVariant[condition.clinical_status] || "outline"}>
                {condition.clinical_status}
              </Badge>
            </TableCell>
            <TableCell>
              {condition.onset_date
                ? new Date(condition.onset_date).toLocaleDateString()
                : "—"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
