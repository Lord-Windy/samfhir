import { Outlet } from "react-router"
import { Header } from "./Header"
import { Nav } from "./Nav"

export function AppLayout() {
  return (
    <div className="flex h-screen flex-col bg-background">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Nav />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
