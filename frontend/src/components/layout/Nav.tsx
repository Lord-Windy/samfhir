import { NavLink } from "react-router"
import { Search, Database } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", label: "Search", icon: Search },
  { to: "/cache", label: "Cache Stats", icon: Database },
]

export function Nav() {
  return (
    <nav className="flex h-full w-48 flex-col border-r bg-card py-4">
      <div className="space-y-1 px-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
