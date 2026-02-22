import { Outlet } from 'react-router'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto py-8">
        <Outlet />
      </div>
    </div>
  )
}
