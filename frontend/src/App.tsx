import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { AppLayout } from './layouts/AppLayout'
import { SearchPage } from './pages/SearchPage'
import { DashboardPage } from './pages/DashboardPage'
import { ObservationFormPage } from './pages/ObservationFormPage'
import { CacheStatsPage } from './pages/CacheStatsPage'

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
    element: <AppLayout />,
    children: [
      {
        path: '/',
        element: <SearchPage />,
      },
      {
        path: '/patients/:id',
        element: <DashboardPage />,
      },
      {
        path: '/patients/:id/observations/new',
        element: <ObservationFormPage />,
      },
      {
        path: '/cache',
        element: <CacheStatsPage />,
      },
    ],
  },
])

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
