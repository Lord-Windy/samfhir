import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background text-foreground">
        <div className="container mx-auto py-8">
          <h1 className="text-3xl font-bold">SamFHIR</h1>
          <p className="mt-2 text-muted-foreground">
            FHIR R4 Patient Data Viewer
          </p>
        </div>
      </div>
    </QueryClientProvider>
  )
}
