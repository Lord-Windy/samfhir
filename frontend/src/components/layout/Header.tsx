import { ConnectionStatus } from "./ConnectionStatus"

export function Header() {
  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <h1 className="text-lg font-semibold">SamFHIR</h1>
      <ConnectionStatus />
    </header>
  )
}
