import { useState } from "react"
import { useNavigate } from "react-router"
import { Search } from "lucide-react"
import { useSearchPatients } from "@/hooks/use-patients"
import { useDebounce } from "@/hooks/use-debounce"
import { PatientSearchResults } from "@/components/PatientSearchResults"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"

export function SearchPage() {
  const [nameQuery, setNameQuery] = useState("")
  const [patientId, setPatientId] = useState("")
  const debouncedName = useDebounce(nameQuery, 300)
  const navigate = useNavigate()

  const {
    data: patients,
    isLoading,
    isError,
    error,
  } = useSearchPatients(debouncedName.trim() || undefined)

  function handleIdLookup(e: React.FormEvent) {
    e.preventDefault()
    const id = patientId.trim()
    if (id) {
      navigate(`/patients/${id}`)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Patient Search</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Search by name or look up a patient directly by ID.
        </p>
      </div>

      <Tabs defaultValue="search">
        <TabsList>
          <TabsTrigger value="search">Search by Name</TabsTrigger>
          <TabsTrigger value="lookup">Lookup by ID</TabsTrigger>
        </TabsList>

        <TabsContent value="search" className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label htmlFor="name-search">Patient name</Label>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
              <Input
                id="name-search"
                placeholder="e.g. Smith"
                value={nameQuery}
                onChange={(e) => setNameQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {isLoading && (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-[72px] w-full" />
              <Skeleton className="h-[72px] w-full" />
              <Skeleton className="h-[72px] w-full" />
            </div>
          )}

          {isError && (
            <Alert variant="destructive">
              <AlertTitle>Search failed</AlertTitle>
              <AlertDescription>
                {error instanceof Error ? error.message : "An unexpected error occurred."}
              </AlertDescription>
            </Alert>
          )}

          {patients && <PatientSearchResults patients={patients} />}
        </TabsContent>

        <TabsContent value="lookup" className="space-y-4 pt-4">
          <form onSubmit={handleIdLookup} className="flex items-end gap-3">
            <div className="flex-1 space-y-2">
              <Label htmlFor="patient-id">Patient ID</Label>
              <Input
                id="patient-id"
                placeholder="e.g. 592912"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={!patientId.trim()}>
              View
            </Button>
          </form>
        </TabsContent>
      </Tabs>
    </div>
  )
}
