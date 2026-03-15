import { Link, useParams } from "react-router"
import { usePatientSummary } from "@/hooks/use-patients"
import { PatientDemographics } from "@/components/patient"
import {
  ConditionsTable,
  ObservationsTable,
  MedicationsTable,
  AllergiesTable,
} from "@/components/clinical"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, Plus, RefreshCw } from "lucide-react"

export function DashboardPage() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, error, isError, refetch, isFetching, dataUpdatedAt } = usePatientSummary(id ?? "")

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-36" />
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </CardContent>
        </Card>
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (isError) {
    const isNotFound = error && typeof error === "object" && "status" in error && error.status === 404
    const isServiceUnavailable =
      error &&
      typeof error === "object" &&
      "status" in error &&
      (error.status === 502 || error.status === 503)

    if (isNotFound) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Patient Not Found</AlertTitle>
          <AlertDescription>
            The patient with ID "{id}" could not be found.
          </AlertDescription>
        </Alert>
      )
    }

    if (isServiceUnavailable) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Service Unavailable</AlertTitle>
          <AlertDescription>
            The FHIR server is currently unavailable. Please try again later.
          </AlertDescription>
        </Alert>
      )
    }

    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          An unexpected error occurred while loading patient data.
        </AlertDescription>
      </Alert>
    )
  }

  if (!data) {
    return null
  }

  const { patient, active_conditions, recent_observations, active_medications, allergies } = data

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          {patient.given_name} {patient.family_name}
        </h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => refetch()}
            disabled={isFetching}
            aria-label="Refresh patient data"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          </Button>
          <Button asChild>
            <Link to={`/patients/${id}/observations/new`}>
              <Plus className="h-4 w-4" />
              Add Observation
            </Link>
          </Button>
        </div>
      </div>

      <PatientDemographics patient={patient} lastUpdated={dataUpdatedAt} />

      <Tabs defaultValue="conditions">
        <TabsList>
          <TabsTrigger value="conditions">
            Conditions ({active_conditions.length})
          </TabsTrigger>
          <TabsTrigger value="observations">
            Observations ({recent_observations.length})
          </TabsTrigger>
          <TabsTrigger value="medications">
            Medications ({active_medications.length})
          </TabsTrigger>
          <TabsTrigger value="allergies">
            Allergies ({allergies.length})
          </TabsTrigger>
        </TabsList>
        <TabsContent value="conditions">
          <Card>
            <CardContent className="pt-6">
              <ConditionsTable conditions={active_conditions} />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="observations">
          <Card>
            <CardContent className="pt-6">
              <ObservationsTable observations={recent_observations} />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="medications">
          <Card>
            <CardContent className="pt-6">
              <MedicationsTable medications={active_medications} />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="allergies">
          <Card>
            <CardContent className="pt-6">
              <AllergiesTable allergies={allergies} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
