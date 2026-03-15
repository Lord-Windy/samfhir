import { createBrowserRouter, RouterProvider } from "react-router"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "@/components/ui/sonner"
import { AppLayout, ErrorBoundary, GlobalLoadingBar, OfflineQueueProvider } from "@/components/layout"
import { SearchPage, CacheStatsPage } from "@/pages"
import { DashboardPage } from "@/pages/DashboardPage"
import { ObservationFormPage } from "@/pages/ObservationFormPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <ErrorBoundary />,
    children: [
      {
        index: true,
        element: <SearchPage />,
      },
      {
        path: "patients/:id",
        element: <DashboardPage />,
      },
      {
        path: "patients/:id/observations/new",
        element: <ObservationFormPage />,
      },
      {
        path: "cache",
        element: <CacheStatsPage />,
      },
    ],
  },
])

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <OfflineQueueProvider>
        <GlobalLoadingBar />
        <RouterProvider router={router} />
        <Toaster />
      </OfflineQueueProvider>
    </QueryClientProvider>
  )
}
