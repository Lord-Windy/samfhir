import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { ObservationResponse } from "@/types/api"

interface ObservationsTableProps {
  observations: ObservationResponse[]
}

export function ObservationsTable({ observations }: ObservationsTableProps) {
  if (observations.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-8">
        No observations found
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Observation</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {observations.map((observation) => (
          <TableRow key={observation.id}>
            <TableCell className="font-medium">{observation.display}</TableCell>
            <TableCell>
              {observation.value}
              {observation.unit && ` ${observation.unit}`}
            </TableCell>
            <TableCell>
              {observation.effective_date
                ? new Date(observation.effective_date).toLocaleDateString()
                : "—"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
